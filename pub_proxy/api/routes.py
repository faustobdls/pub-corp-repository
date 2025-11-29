from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context, url_for, redirect
from injector import inject, Injector

from pub_proxy.core.use_cases.proxy_package_use_case import ProxyPackageUseCase
from pub_proxy.core.use_cases.upload_package_use_case import UploadPackageUseCase
from pub_proxy.core.use_cases.download_package_use_case import DownloadPackageUseCase
from pub_proxy.core.use_cases.list_packages_use_case import ListPackagesUseCase
from pub_proxy.core.services.auth_service import AuthService

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
    def get_package_info(package_name: str, proxy_use_case: ProxyPackageUseCase):
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
    def get_package_version(package_name: str, version: str, proxy_use_case: ProxyPackageUseCase):
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
    @inject
    def download_package(package_name: str, version: str, download_use_case: DownloadPackageUseCase, auth_service: AuthService):
        """
        Download a package archive.
        
        This endpoint returns the archive file for a specific version of a package.
        It first checks if the package is available in the GCP bucket, and if not,
        it proxies the request to pub.dev and caches the result in the bucket.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @param download_use_case: The use case for downloading packages.
        @param auth_service: The service for authentication.
        @return: The package archive file.
        """
        # Check authentication
        auth_header = request.headers.get('Authorization')
        
        # Debug logging
        if not auth_header:
            print(f"DEBUG: Missing Authorization header for download. Headers: {dict(request.headers)}")
        elif not auth_header.startswith('Bearer '):
            print(f"DEBUG: Invalid Authorization header format: {auth_header}")
            
        if not auth_header or not auth_header.startswith('Bearer '):
            # Check if it's a browser request (optional, for now strict)
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        token = auth_header.split(' ')[1]
        if not auth_service.validate_token(token):
            return jsonify({'error': 'Invalid token'}), 401

        try:
            file_path_or_stream, is_stream = download_use_case.execute(package_name, version)
            
            if is_stream:
                return Response(
                    stream_with_context(file_path_or_stream),
                    content_type='application/octet-stream'
                )
            else:
                return send_file(file_path_or_stream, mimetype='application/octet-stream')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api_bp.route('/api/packages/versions/new', methods=['GET'])
    @inject
    def new_package_version(auth_service: AuthService):
        """
        Initiate the package upload process for dart pub publish.
        
        @param auth_service: The service for authentication.
        @return: JSON with upload URL and fields.
        """
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        token = auth_header.split(' ')[1]
        if not auth_service.validate_token(token):
            return jsonify({'error': 'Invalid token'}), 401
            
        # Return the upload URL
        # Note: _external=True is important to return the full URL
        upload_url = url_for('api.upload_package_new', _external=True)
        
        return jsonify({
            'url': upload_url,
            'fields': {}
        })

    @api_bp.route('/api/packages/versions/newUpload', methods=['POST'])
    @inject
    def upload_package_new(upload_use_case: UploadPackageUseCase, auth_service: AuthService):
        """
        Handle the package upload for dart pub publish.
        
        @param upload_use_case: The use case for uploading packages.
        @param auth_service: The service for authentication.
        @return: Redirect to finish endpoint.
        """
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        token = auth_header.split(' ')[1]
        if not auth_service.validate_token(token):
            return jsonify({'error': 'Invalid token'}), 401

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        try:
            # Execute upload (metadata extracted from tarball)
            upload_use_case.execute(None, None, file)
            
            # Redirect to finish endpoint
            finish_url = url_for('api.upload_package_finish', _external=True)
            return redirect(finish_url)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/api/packages/versions/newUploadFinish', methods=['GET'])
    def upload_package_finish():
        """
        Finalize the package upload process.
        
        @return: Success message.
        """
        return jsonify({'success': {'message': 'Successfully uploaded package.'}})

    @api_bp.route('/api/packages', methods=['POST'])
    @inject
    def upload_package(upload_use_case: UploadPackageUseCase, auth_service: AuthService):
        """
        Upload a package to the repository (legacy/manual endpoint).
        
        This endpoint allows uploading a package archive to the repository.
        The package will be stored in the GCP bucket and made available for download.
        
        @param upload_use_case: The use case for uploading packages.
        @param auth_service: The service for authentication.
        @return: A JSON response with the result of the upload operation.
        """
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        token = auth_header.split(' ')[1]
        if not auth_service.validate_token(token):
            return jsonify({'error': 'Invalid token'}), 401
            
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Optional form fields (if not provided, extracted from tarball)
        package_name = request.form.get('package_name')
        version = request.form.get('version')
        
        try:
            result = upload_use_case.execute(package_name, version, file)
            return jsonify(result), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Register the blueprint with the application
    app.register_blueprint(api_bp)
            
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