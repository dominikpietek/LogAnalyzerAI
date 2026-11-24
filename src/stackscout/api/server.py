from stackscout.adapters.filesystem_workspace import FileSystemWorkspace
from stackscout.api.app import create_app
from stackscout.api.settings import Settings

settings = Settings()
app = create_app(FileSystemWorkspace(settings.project_root))
