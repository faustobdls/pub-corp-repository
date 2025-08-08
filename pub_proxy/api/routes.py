from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
from injector import inject

from pub_proxy.core.use_cases.proxy_package_use_case import ProxyPackageUseCase
from pub_proxy.core.use_cases.upload_package_use_case import UploadPackageUseCase
from pub_proxy.core.use_cases.download_package_use_case import DownloadPackageUseCase
from pub_proxy.core.use_cases.list_packages_use_case import ListPackagesUseCase

"""
Routes module for the Pub Corp Repository API.

This module defines the routes for the API, including endpoints for proxying requests to pub.dev,
uploading packages to the GCP bucket, downloading packages from the bucket, and listing available packages.

@example
```python
from pub_proxy.api.routes import register_routes
from injector import Injector

injector = Injector(...)
register_routes(app, injector)
```
"""


def register_routes(app):
    """
    Register routes for the application.
    
    This function creates a Blueprint for the API routes and registers it with the Flask application.
    
    @param app: The Flask application instance.
    """
    api_bp = Blueprint('api', __name__)
    
    @api_bp.route('/api/packages', methods=['GET'])
    @inject
    def list_packages(list_use_case: ListPackagesUseCase):
        """
        List available packages.
        
        This endpoint returns a list of packages available in the repository.
        It can filter packages by name, version, and other criteria.
        It first checks storage (GCP or local), then fetches from pub.dev if needed.
        
        @param list_use_case: The use case for listing packages.
        @return: A JSON response with the list of packages.
        """
        query = request.args.get('q', '')
        page = int(request.args.get('page', '1'))
        page_size = int(request.args.get('page_size', '10'))
        
        try:
            # Use the list use case to get packages (checks storage first, then pub.dev)
            packages = list_use_case.execute(query, page, page_size)
            return jsonify(packages)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/api/packages/<package_name>', methods=['GET'])
    @inject
    def get_package_info(package_name, proxy_use_case: ProxyPackageUseCase):
        """
        Get information about a package.
        
        This endpoint returns information about a specific package, including its versions,
        dependencies, and other metadata. It first checks if the package exists in storage
        (GCP or local), and if not, fetches from pub.dev, stores it, and returns the result.
        
        @param package_name: The name of the package.
        @param proxy_use_case: The use case for proxying package requests.
        @return: A JSON response with the package information.
        """
        try:
            # Use the proxy use case to get package info (checks storage first, then pub.dev)
            package_info = proxy_use_case.get_package_info(package_name)
            return jsonify(package_info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/api/packages/<package_name>/versions/<version>', methods=['GET'])
    @inject
    def get_package_version(package_name, version, proxy_use_case: ProxyPackageUseCase):
        """
        Get information about a specific version of a package.
        
        This endpoint returns information about a specific version of a package,
        including its dependencies and other metadata. It first checks if the version
        exists in storage (GCP or local), and if not, fetches from pub.dev, stores it, and returns the result.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @param proxy_use_case: The use case for proxying package requests.
        @return: A JSON response with the package version information.
        """
        try:
            # Use the proxy use case to get package version info (checks storage first, then pub.dev)
            version_info = proxy_use_case.get_package_version(package_name, version)
            return jsonify(version_info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/api/packages/<package_name>/versions/<version>/archive.tar.gz', methods=['GET'])
    def download_package(package_name, version):
        """
        Download a package archive.
        
        This endpoint returns the archive file for a specific version of a package.
        It first checks if the package is available in the GCP bucket, and if not,
        it proxies the request to pub.dev and caches the result in the bucket.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: The package archive file.
        """
        try:
            # Return a simple response for now
            return jsonify({'message': 'Package download not implemented yet'}), 501
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/api/packages', methods=['POST'])
    def upload_package():
        """
        Upload a package to the repository.
        
        This endpoint allows uploading a package archive to the repository.
        The package will be stored in the GCP bucket and made available for download.
        
        @return: A JSON response with the result of the upload operation.
        """
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        package_name = request.form.get('package_name')
        version = request.form.get('version')
        
        if not package_name or not version:
            return jsonify({'error': 'Package name and version are required'}), 400
        
        try:
            # Return a simple response for now
            return jsonify({'message': 'Package upload not implemented yet'}), 501
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Register the blueprint with the application
    app.register_blueprint(api_bp)
    
    # Add routes for Flutter pub client
    @app.route('/packages/<package_name>', methods=['GET'])
    def get_package(package_name):
        """
        Get package information for Flutter pub client.
        
        This endpoint proxies requests to pub.dev for the Flutter pub client.
        
        @param package_name: The name of the package.
        @return: The response from pub.dev.
        """
        try:
            import requests
            from flask import Response, stream_with_context
            
            # Default pub.dev URL
            pub_dev_url = "https://pub.dev"
            
            # Construct the full URL
            url = f"{pub_dev_url}/packages/{package_name}"
            
            # Forward the request to pub.dev
            resp = requests.request(
                method=request.method,
                url=url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                stream=True
            )
            
            # Create a Flask response from the pub.dev response
            response = Response(
                stream_with_context(resp.iter_content(chunk_size=1024)),
                status=resp.status_code,
                content_type=resp.headers.get('Content-Type', 'text/plain')
            )
            
            # Copy headers from the pub.dev response
            for key, value in resp.headers.items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
                    
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/packages/<package_name>', methods=['GET'])
    def get_package_api(package_name):
        """
        Get package information for Flutter pub client (API route).
        
        This endpoint proxies requests to pub.dev API for the Flutter pub client.
        
        @param package_name: The name of the package.
        @return: The response from pub.dev API.
        """
        try:
            import requests
            from flask import Response, stream_with_context
            
            # Default pub.dev URL
            pub_dev_url = "https://pub.dev"
            
            # Construct the full URL
            url = f"{pub_dev_url}/api/packages/{package_name}"
            
            # Forward the request to pub.dev
            resp = requests.request(
                method=request.method,
                url=url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                stream=True
            )
            

            # Create a Flask response from the pub.dev response
            response = Response(
                stream_with_context(resp.iter_content(chunk_size=1024)),
                status=resp.status_code,
                content_type=resp.headers.get('Content-Type', 'application/json')
            )
            
            # Copy headers from the pub.dev response
            for key, value in resp.headers.items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
                    
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/packages/<package_name>/versions/<version>', methods=['GET'])
    def get_package_version_api(package_name, version):
        """
        Get package version information for Flutter pub client (API route).
        
        This endpoint proxies requests to pub.dev API for the Flutter pub client.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: The response from pub.dev API.
        """
        try:
            import requests
            from flask import Response, stream_with_context
            
            # Default pub.dev URL
            pub_dev_url = "https://pub.dev"
            
            # Construct the full URL
            url = f"{pub_dev_url}/api/packages/{package_name}/versions/{version}"
            
            # Forward the request to pub.dev
            resp = requests.request(
                method=request.method,
                url=url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                stream=True
            )
            
            # Create a Flask response from the pub.dev response
            response = Response(
                stream_with_context(resp.iter_content(chunk_size=1024)),
                status=resp.status_code,
                content_type=resp.headers.get('Content-Type', 'application/json')
            )
            
            # Copy headers from the pub.dev response
            for key, value in resp.headers.items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
                    
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/packages/<package_name>/versions/<version>/archive.tar.gz', methods=['GET'])
    def download_package_archive(package_name, version):
        """
        Download a package archive for Flutter pub client.
        
        This endpoint proxies requests to pub.dev for downloading package archives.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: The package archive file.
        """
        try:
            import requests
            from flask import Response, stream_with_context
            
            # Default pub.dev URL
            pub_dev_url = "https://pub.dev"
            
            # Construct the full URL
            url = f"{pub_dev_url}/api/packages/{package_name}/versions/{version}/archive.tar.gz"
            
            # Forward the request to pub.dev
            resp = requests.request(
                method=request.method,
                url=url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                stream=True
            )
            
            # Create a Flask response from the pub.dev response
            response = Response(
                stream_with_context(resp.iter_content(chunk_size=1024)),
                status=resp.status_code,
                content_type='application/octet-stream'
            )
            
            # Copy headers from the pub.dev response
            for key, value in resp.headers.items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
                    
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    # Add a catch-all route to proxy all other requests to pub.dev
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def proxy(path):
        """
        Proxy requests to pub.dev.
        
        This endpoint proxies all requests that don't match other routes to pub.dev.
        It allows the application to act as a transparent proxy for the pub.dev API.
        
        @param path: The path to proxy to pub.dev.
        @return: The response from pub.dev.
        """
        try:
            import requests
            from flask import Response, stream_with_context
            
            # Default pub.dev URL
            pub_dev_url = "https://pub.dev"
            
            # Construct the full URL
            url = f"{pub_dev_url}/{path}"
            
            # Forward the request to pub.dev
            resp = requests.request(
                method=request.method,
                url=url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                stream=True
            )
            
            # Create a Flask response from the pub.dev response
            response = Response(
                stream_with_context(resp.iter_content(chunk_size=1024)),
                status=resp.status_code,
                content_type=resp.headers.get('Content-Type', 'text/plain')
            )
            
            # Copy headers from the pub.dev response
            for key, value in resp.headers.items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
                    
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500