# src/generators/transaction/Beschaffungsprozess/batch/master_controller.py

from datetime import datetime, timedelta
import calendar
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from pathlib import Path

from src.generators.transaction.Beschaffungsprozess.batch.create_batch_purchase_order import BatchPurchaseOrderGenerator
from src.generators.transaction.Beschaffungsprozess.batch.create_batch_purchase_receipt import \
    BatchPurchaseReceiptGenerator
from src.generators.transaction.Beschaffungsprozess.batch.create_batch_purchase_invoice import \
    BatchPurchaseInvoiceGenerator
from src.generators.transaction.Beschaffungsprozess.batch.create_batch_payment_entry import BatchPaymentEntryGenerator
from src.config.settings import OUTPUT_DIR


@dataclass
class ProcessConfig:
    """Configuration for the procurement process."""
    start_date: datetime
    end_date: datetime
    total_orders: int
    batch_size: Optional[int] = None


class ProcurementMasterController:
    """Master controller for orchestrating the procurement process."""

    def __init__(self):
        self.logger = logging.getLogger('ProcurementMasterController')
        self._initialize_logging()

    def _initialize_logging(self):
        """Initialize logging configuration"""
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler
        log_dir = OUTPUT_DIR / 'logs' / 'master_controller'
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f'master_controller_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def distribute_orders_by_month(self, config: ProcessConfig) -> Dict[str, int]:
        """Distribute total orders across months based on date range."""
        total_months = self._calculate_months_between_dates(config.start_date, config.end_date)
        orders_per_month = {}

        # Calculate base orders per month and remaining orders
        base_orders = config.total_orders // total_months
        remaining_orders = config.total_orders % total_months

        current_date = config.start_date
        while current_date <= config.end_date:
            month_key = current_date.strftime("%Y-%m")
            orders_per_month[month_key] = base_orders

            # Distribute remaining orders
            if remaining_orders > 0:
                orders_per_month[month_key] += 1
                remaining_orders -= 1

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        return orders_per_month

    def _calculate_months_between_dates(self, start_date: datetime, end_date: datetime) -> int:
        """Calculate number of months between two dates."""
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1

    def _get_month_date_range(self, year: int, month: int) -> tuple[datetime, datetime]:
        """Get start and end date for a specific month."""
        start_date = datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day, 23, 59, 59)
        return start_date, end_date

    def process_month(self, year: int, month: int, num_orders: int) -> bool:
        """Process all procurement documents for a specific month."""
        start_date, end_date = self._get_month_date_range(year, month)

        self.logger.info(f"Starting procurement process for {year}-{month:02d} "
                         f"with {num_orders} orders")

        try:
            # 1. Generate Purchase Orders
            po_generator = BatchPurchaseOrderGenerator()
            po_generator.configure(start_date, end_date, num_orders)

            if not po_generator.process():
                self.logger.error(f"Failed to generate purchase orders for {year}-{month:02d}")
                return False

            purchase_orders = po_generator.get_successful_orders()
            self.logger.info(f"Successfully generated {len(purchase_orders)} purchase orders")

            # 2. Generate Purchase Receipts based on Purchase Orders
            if purchase_orders:
                pr_generator = BatchPurchaseReceiptGenerator()
                pr_generator.configure(start_date, end_date, purchase_orders)

                if not pr_generator.process():
                    self.logger.error(f"Failed to generate purchase receipts for {year}-{month:02d}")
                    return False

                purchase_receipts = pr_generator.get_successful_receipts()
                self.logger.info(f"Successfully generated {len(purchase_receipts)} purchase receipts")

                # 3. Generate Purchase Invoices based on Purchase Receipts
                if purchase_receipts:
                    pi_generator = BatchPurchaseInvoiceGenerator()
                    pi_generator.configure(start_date, end_date, purchase_receipts)

                    if not pi_generator.process():
                        self.logger.error(f"Failed to generate purchase invoices for {year}-{month:02d}")
                        return False

                    purchase_invoices = pi_generator.get_successful_invoices()
                    self.logger.info(f"Successfully generated {len(purchase_invoices)} purchase invoices")

                    # 4. Generate Payment Entries based on Purchase Invoices
                    if purchase_invoices:
                        pe_generator = BatchPaymentEntryGenerator()
                        pe_generator.configure(start_date, end_date, purchase_invoices)

                        if not pe_generator.process():
                            self.logger.error(f"Failed to generate payment entries for {year}-{month:02d}")
                            return False

                        payment_entries = pe_generator.get_successful_payments()
                        self.logger.info(f"Successfully generated {len(payment_entries)} payment entries")

            self.logger.info(f"Successfully completed procurement process for {year}-{month:02d}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing month {year}-{month:02d}: {str(e)}")
            return False

    def run_procurement_process(self, config: ProcessConfig) -> bool:
        """Main method to run the complete procurement process."""
        self.logger.info(f"Starting procurement process for period: "
                         f"{config.start_date.date()} to {config.end_date.date()}")

        try:
            # Distribute orders across months
            monthly_distribution = self.distribute_orders_by_month(config)

            success_count = 0
            # Process each month sequentially
            for month_key, num_orders in monthly_distribution.items():
                year, month = map(int, month_key.split('-'))
                if self.process_month(year, month, num_orders):
                    success_count += 1

            total_months = len(monthly_distribution)
            self.logger.info(f"Completed procurement process: {success_count}/{total_months} months successful")

            return success_count == total_months

        except Exception as e:
            self.logger.error(f"Procurement process failed: {str(e)}")
            return False


def main():
    """Example usage of the procurement master controller."""
    # Configure process parameters
    config = ProcessConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        total_orders=10
    )

    # Initialize and run controller
    controller = ProcurementMasterController()
    success = controller.run_procurement_process(config)

    print(f"Procurement process {'completed successfully' if success else 'failed'}")


if __name__ == "__main__":
    main()
