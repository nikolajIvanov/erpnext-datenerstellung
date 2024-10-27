# Environment Setup

## Environment Variables
The project uses environment variables for configuration. To set these up:

1. Copy `.env.example` to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual API key:
   ```
   ERP_API_KEY=your_actual_api_key
   ```

Note: Never commit the `.env` file to version control! It contains sensitive information.