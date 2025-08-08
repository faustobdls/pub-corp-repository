# Pub Corp Repository

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Pub Corp Repository is an open-source Python Flask application that acts as a proxy for pub.dev, with an additional layer of caching and management using either a Google Cloud Platform (GCP) bucket or a local file system.

This project is designed to allow companies to have a private repository of Dart/Flutter packages, while still being able to access public packages from pub.dev. **Perfect for internal company use** - you can deploy it within your organization to have better control over package dependencies and reduce external dependencies.

## Features

- Acts as a proxy for pub.dev.
- Caches packages in a GCP bucket or local file system to reduce latency and dependency on pub.dev.
- Allows for hosting private packages.
- Built with Clean Architecture and SOLID principles.

## Project Structure

The project follows the principles of Clean Architecture, separating concerns into different layers:

- `run.py`: The entry point of the application.
- `requirements.txt`: The list of dependencies.
- `config.py`: The configuration file for the application.
- `pub_proxy/`: The main application package.
  - `api/`: The presentation layer, containing the Flask routes.
  - `core/`: The core of the application, containing the business logic (use cases and entities).
  - `infrastructure/`: The infrastructure layer, containing the implementation of external services (GCP bucket, pub.dev client).

## Getting Started

### Prerequisites

- Python 3.8+
- For GCP storage mode: A Google Cloud Platform account with a configured bucket.
- For local storage mode: Sufficient disk space for package storage.

## Testing

To run the tests for the application, you can use the provided script or run pytest directly:

```bash
# Usando o script
./run_tests.sh

# Ou diretamente com pytest
python -m pytest
```

The test suite includes unit tests for all layers of the application, ensuring that the business logic, API endpoints, and storage implementations work as expected. The tests cover both the GCP and local storage implementations, allowing you to verify that both storage options work correctly.

### Installation

1. Clone the repository:
    ```bash
   git clone https://github.com/your-username/pub-corp-repository.git
   cd pub-corp-repository
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the application by creating a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file to set your preferences:
   - For local storage (default): Set `STORAGE_TYPE=local` and configure `LOCAL_STORAGE_DIR`
   - For GCP storage: Set `STORAGE_TYPE=gcp` and configure your GCP credentials and bucket name
   - Server configuration: Set `HOST` and `PORT` to configure the server address (defaults to 0.0.0.0:5000)

6. Run the application:
   ```bash
   python run.py
   ```

## Usage

To use this proxy with the `pub` CLI, you need to set the `PUB_HOSTED_URL` environment variable:

```bash
export PUB_HOSTED_URL=http://localhost:5000
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is perfect for internal company use as it:
- ✅ Allows commercial use
- ✅ Allows modification and distribution
- ✅ Allows private use
- ✅ No copyleft requirements
- ✅ Simple and permissive

You can freely use, modify, and distribute this software within your organization without any restrictions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Now, when you run `flutter pub get` or `dart pub get`, the CLI will use your proxy instead of the official pub.dev.