"""Docker Integration - Feature 30.

Docker utilities:
- List containers/images
- Build images
- Run containers
- Docker Compose support
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Container:
    """A Docker container."""
    id: str
    name: str
    image: str
    status: str
    ports: str
    created: str

    @classmethod
    def from_docker_json(cls, data: Dict[str, Any]) -> "Container":
        return cls(
            id=data.get("ID", "")[:12],
            name=data.get("Names", ""),
            image=data.get("Image", ""),
            status=data.get("Status", ""),
            ports=data.get("Ports", ""),
            created=data.get("CreatedAt", ""),
        )


@dataclass
class Image:
    """A Docker image."""
    id: str
    repository: str
    tag: str
    size: str
    created: str

    @classmethod
    def from_docker_json(cls, data: Dict[str, Any]) -> "Image":
        return cls(
            id=data.get("ID", "")[:12],
            repository=data.get("Repository", ""),
            tag=data.get("Tag", ""),
            size=data.get("Size", ""),
            created=data.get("CreatedAt", ""),
        )


@dataclass
class DockerResult:
    """Result of a Docker operation."""
    success: bool
    output: str = ""
    error: str = ""
    command: str = ""


class DockerTools:
    """Docker integration utilities."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize Docker tools."""
        self.working_dir = working_dir or Path.cwd()
        self._docker_available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if Docker is available."""
        if self._docker_available is None:
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    timeout=5,
                )
                self._docker_available = result.returncode == 0
            except (subprocess.SubprocessError, FileNotFoundError):
                self._docker_available = False
        return self._docker_available

    def _run_docker(
        self,
        args: List[str],
        timeout: int = 60,
        working_dir: Optional[Path] = None,
    ) -> DockerResult:
        """Run a Docker command."""
        cmd = ["docker"] + args
        result = DockerResult(success=False, command=" ".join(cmd))

        try:
            proc = subprocess.run(
                cmd,
                cwd=working_dir or self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            result.output = proc.stdout
            result.error = proc.stderr
            result.success = proc.returncode == 0

        except subprocess.TimeoutExpired:
            result.error = "Command timed out"
        except FileNotFoundError:
            result.error = "Docker not found"
        except Exception as e:
            result.error = str(e)

        return result

    def list_containers(self, all: bool = False) -> List[Container]:
        """
        List Docker containers.

        Args:
            all: Include stopped containers

        Returns:
            List of containers
        """
        args = ["ps", "--format", "{{json .}}"]
        if all:
            args.append("-a")

        result = self._run_docker(args)

        if not result.success:
            return []

        containers = []
        for line in result.output.strip().split("\n"):
            if line:
                try:
                    data = json.loads(line)
                    containers.append(Container.from_docker_json(data))
                except json.JSONDecodeError:
                    pass

        return containers

    def list_images(self) -> List[Image]:
        """List Docker images."""
        result = self._run_docker(["images", "--format", "{{json .}}"])

        if not result.success:
            return []

        images = []
        for line in result.output.strip().split("\n"):
            if line:
                try:
                    data = json.loads(line)
                    images.append(Image.from_docker_json(data))
                except json.JSONDecodeError:
                    pass

        return images

    def build(
        self,
        tag: str,
        dockerfile: str = "Dockerfile",
        context: str = ".",
        build_args: Optional[Dict[str, str]] = None,
        no_cache: bool = False,
    ) -> DockerResult:
        """
        Build a Docker image.

        Args:
            tag: Image tag
            dockerfile: Dockerfile path
            context: Build context
            build_args: Build arguments
            no_cache: Disable cache

        Returns:
            DockerResult
        """
        args = ["build", "-t", tag, "-f", dockerfile]

        if no_cache:
            args.append("--no-cache")

        if build_args:
            for key, value in build_args.items():
                args.extend(["--build-arg", f"{key}={value}"])

        args.append(context)

        return self._run_docker(args, timeout=600)

    def run(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
        detach: bool = True,
        command: Optional[str] = None,
    ) -> DockerResult:
        """
        Run a Docker container.

        Args:
            image: Image to run
            name: Container name
            ports: Port mappings (host:container)
            volumes: Volume mappings (host:container)
            env: Environment variables
            detach: Run in background
            command: Command to run

        Returns:
            DockerResult
        """
        args = ["run"]

        if detach:
            args.append("-d")

        if name:
            args.extend(["--name", name])

        if ports:
            for host_port, container_port in ports.items():
                args.extend(["-p", f"{host_port}:{container_port}"])

        if volumes:
            for host_path, container_path in volumes.items():
                args.extend(["-v", f"{host_path}:{container_path}"])

        if env:
            for key, value in env.items():
                args.extend(["-e", f"{key}={value}"])

        args.append(image)

        if command:
            args.extend(command.split())

        return self._run_docker(args)

    def stop(self, container: str) -> DockerResult:
        """Stop a container."""
        return self._run_docker(["stop", container])

    def start(self, container: str) -> DockerResult:
        """Start a container."""
        return self._run_docker(["start", container])

    def remove_container(self, container: str, force: bool = False) -> DockerResult:
        """Remove a container."""
        args = ["rm"]
        if force:
            args.append("-f")
        args.append(container)
        return self._run_docker(args)

    def remove_image(self, image: str, force: bool = False) -> DockerResult:
        """Remove an image."""
        args = ["rmi"]
        if force:
            args.append("-f")
        args.append(image)
        return self._run_docker(args)

    def logs(self, container: str, tail: int = 100) -> DockerResult:
        """Get container logs."""
        return self._run_docker(["logs", "--tail", str(tail), container])

    def exec(self, container: str, command: str) -> DockerResult:
        """Execute command in container."""
        return self._run_docker(["exec", container] + command.split())

    def pull(self, image: str) -> DockerResult:
        """Pull an image."""
        return self._run_docker(["pull", image], timeout=300)

    def push(self, image: str) -> DockerResult:
        """Push an image."""
        return self._run_docker(["push", image], timeout=300)

    # Docker Compose support
    def compose_up(
        self,
        file: str = "docker-compose.yml",
        detach: bool = True,
        build: bool = False,
    ) -> DockerResult:
        """
        Start Docker Compose services.

        Args:
            file: Compose file path
            detach: Run in background
            build: Build images before starting

        Returns:
            DockerResult
        """
        args = ["compose", "-f", file, "up"]

        if detach:
            args.append("-d")

        if build:
            args.append("--build")

        return self._run_docker(args, timeout=300)

    def compose_down(self, file: str = "docker-compose.yml", volumes: bool = False) -> DockerResult:
        """Stop Docker Compose services."""
        args = ["compose", "-f", file, "down"]

        if volumes:
            args.append("-v")

        return self._run_docker(args)

    def compose_ps(self, file: str = "docker-compose.yml") -> DockerResult:
        """List Compose services."""
        return self._run_docker(["compose", "-f", file, "ps"])

    def compose_logs(
        self,
        service: Optional[str] = None,
        file: str = "docker-compose.yml",
        tail: int = 100,
    ) -> DockerResult:
        """Get Compose service logs."""
        args = ["compose", "-f", file, "logs", "--tail", str(tail)]
        if service:
            args.append(service)
        return self._run_docker(args)

    def get_info(self) -> Dict[str, Any]:
        """Get Docker system info."""
        result = self._run_docker(["info", "--format", "{{json .}}"])

        if result.success:
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                pass

        return {}

    def get_report(self) -> str:
        """Generate Docker report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  DOCKER STATUS")
        lines.append("=" * 60)
        lines.append("")

        if not self.is_available():
            lines.append("[ERROR] Docker not available")
            lines.append("=" * 60)
            return "\n".join(lines)

        # Get info
        info = self.get_info()
        if info:
            lines.append(f"Docker Version: {info.get('ServerVersion', 'Unknown')}")
            lines.append(f"Containers: {info.get('Containers', 0)} ({info.get('ContainersRunning', 0)} running)")
            lines.append(f"Images: {info.get('Images', 0)}")
            lines.append("")

        # List running containers
        containers = self.list_containers()
        lines.append(f"Running Containers ({len(containers)}):")
        if containers:
            for c in containers[:5]:
                lines.append(f"  - {c.name}: {c.image} ({c.status})")
            if len(containers) > 5:
                lines.append(f"  ... and {len(containers) - 5} more")
        else:
            lines.append("  (none)")
        lines.append("")

        # List images
        images = self.list_images()
        lines.append(f"Images ({len(images)}):")
        if images:
            for i in images[:5]:
                lines.append(f"  - {i.repository}:{i.tag} ({i.size})")
            if len(images) > 5:
                lines.append(f"  ... and {len(images) - 5} more")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_docker_tools: Optional[DockerTools] = None


def get_docker_tools(working_dir: Optional[Path] = None) -> DockerTools:
    """Get or create Docker tools."""
    global _docker_tools
    if _docker_tools is None:
        _docker_tools = DockerTools(working_dir)
    return _docker_tools


# Convenience functions
def docker_ps(all: bool = False) -> List[Container]:
    """List containers."""
    return get_docker_tools().list_containers(all)


def docker_images() -> List[Image]:
    """List images."""
    return get_docker_tools().list_images()


def docker_build(tag: str, **kwargs) -> DockerResult:
    """Build image."""
    return get_docker_tools().build(tag, **kwargs)


def docker_run(image: str, **kwargs) -> DockerResult:
    """Run container."""
    return get_docker_tools().run(image, **kwargs)


def docker_compose_up(**kwargs) -> DockerResult:
    """Start Compose services."""
    return get_docker_tools().compose_up(**kwargs)


def docker_compose_down(**kwargs) -> DockerResult:
    """Stop Compose services."""
    return get_docker_tools().compose_down(**kwargs)
