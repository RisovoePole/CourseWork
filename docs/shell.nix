{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-24.05.tar.gz") {} }:

let
  py = pkgs.python3.withPackages (p: [
    p.python-docx
  ]);
in
pkgs.mkShell {
  buildInputs = [ py pkgs.python3Packages.pip ];

  shellHook = ''
    VENV_DIR=".venv-docx"

    if [ ! -d "$VENV_DIR" ]; then
      ${py}/bin/python3 -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"
    pip install docxcompose
  '';
}