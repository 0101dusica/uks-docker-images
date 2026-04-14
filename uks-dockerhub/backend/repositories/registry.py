import requests
from django.conf import settings


class RegistryService:
    """Service to interact with Docker Distribution (registry:2) HTTP API."""

    def __init__(self):
        self.base_url = settings.REGISTRY_URL

    @staticmethod
    def normalize_name(repo_name):
        """Docker requires repository names to be lowercase."""
        return repo_name.lower()

    def get_catalog(self):
        """Get list of all repositories in the registry."""
        try:
            response = requests.get(f'{self.base_url}/v2/_catalog', timeout=5)
            response.raise_for_status()
            return response.json().get('repositories', [])
        except requests.RequestException:
            return []

    def get_tags(self, repo_name):
        """Get list of tags for a repository."""
        repo_name = self.normalize_name(repo_name)
        try:
            response = requests.get(
                f'{self.base_url}/v2/{repo_name}/tags/list', timeout=5
            )
            response.raise_for_status()
            return response.json().get('tags', []) or []
        except requests.RequestException:
            return []

    def get_manifest(self, repo_name, tag):
        """Get manifest for a specific tag (includes digest and size info)."""
        repo_name = self.normalize_name(repo_name)
        try:
            response = requests.get(
                f'{self.base_url}/v2/{repo_name}/manifests/{tag}',
                headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'},
                timeout=5,
            )
            response.raise_for_status()
            digest = response.headers.get('Docker-Content-Digest', '')
            manifest = response.json()
            total_size = sum(
                layer.get('size', 0) for layer in manifest.get('layers', [])
            )
            return {
                'digest': digest,
                'size': total_size,
                'media_type': manifest.get('mediaType', ''),
            }
        except requests.RequestException:
            return None

    def delete_manifest(self, repo_name, digest):
        """Delete a manifest by digest (effectively deletes the tag)."""
        repo_name = self.normalize_name(repo_name)
        try:
            response = requests.delete(
                f'{self.base_url}/v2/{repo_name}/manifests/{digest}',
                timeout=5,
            )
            return response.status_code == 202
        except requests.RequestException:
            return False

    def get_tag_digest(self, repo_name, tag):
        """Get the digest for a specific tag (needed for deletion)."""
        repo_name = self.normalize_name(repo_name)
        try:
            response = requests.head(
                f'{self.base_url}/v2/{repo_name}/manifests/{tag}',
                headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'},
                timeout=5,
            )
            response.raise_for_status()
            return response.headers.get('Docker-Content-Digest', '')
        except requests.RequestException:
            return None
