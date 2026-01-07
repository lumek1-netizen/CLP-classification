# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"
  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.sqlite
  ];
  # Sets environment variables in the workspace
  env = {
    FLASK_APP = "app.py";
    FLASK_ENV = "development";
  };
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
      "ms-python.debugpy"
    ];
    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        install-dependencies = "pip install -r requirements.txt";
      };
      # Runs when the workspace is (re)started
      onStart = {
        # Optional: commands to run on start
      };
    };
    # Preview configuration
    previews = {
      enable = true;
      previews = {
        web = {
          # Example: run "python app.py" or "flask run --port $PORT --host 0.0.0.0"
          command = ["python" "app.py" "--port" "$PORT" "--host" "0.0.0.0"];
          manager = "web";
          env = {
            # Environment variables for the preview process
            PORT = "$PORT";
          };
        };
      };
    };
  };
}
