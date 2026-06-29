{
    description = "FrogOS report build environment";

    inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        flake-utils.url = "github:numtide/flake-utils";
    };

    outputs =
        {
            nixpkgs,
            flake-utils,
            ...
        }:
        flake-utils.lib.eachDefaultSystem (
            system:
            let
                pkgs = nixpkgs.legacyPackages.${system};

                tex = pkgs.texlive.combine {
                    inherit (pkgs.texlive)
                        amsmath
                        beamer
                        booktabs
                        caption
                        chngcntr
                        etoolbox
                        extsizes
                        fancyvrb
                        float
                        fontspec
                        fvextra
                        geometry
                        graphics
                        hyperref
                        latexmk
                        mathtools
                        microtype
                        minted
                        newfloat
                        polyglossia
                        scheme-small
                        titlesec
                        tocloft
                        tools
                        xcolor
                        xetex
                        xurl
                        ;
                };

                buildInputs = with pkgs; [
                    coreutils
                    graphviz
                    python3Packages.pygments
                    tex
                ];

                renderGraphs = ''
                    dot -Tpdf images/architecture.dot -o images/architecture.pdf
                    dot -Tpdf images/state-empty.dot -o images/state-empty.pdf
                    dot -Tpdf images/state-desired.dot -o images/state-desired.pdf
                    dot -Tpdf images/state-current.dot -o images/state-current.pdf
                    dot -Tpdf images/plan-example.dot -o images/plan-example.pdf
                '';

                buildReport = pkgs.writeShellApplication {
                    name = "build-frogos-report";
                    runtimeInputs = buildInputs;
                    text = ''
                        ${renderGraphs}

                        test -f bibliography.bib || : > bibliography.bib

                        xelatex -shell-escape -interaction=nonstopmode -halt-on-error report.tex
                        xelatex -shell-escape -interaction=nonstopmode -halt-on-error report.tex
                        xelatex -shell-escape -interaction=nonstopmode -halt-on-error report.tex
                    '';
                };

                buildPresentation = pkgs.writeShellApplication {
                    name = "build-frogos-presentation";
                    runtimeInputs = buildInputs;
                    text = ''
                        ${renderGraphs}

                        xelatex -shell-escape -interaction=nonstopmode -halt-on-error presentation.tex
                        xelatex -shell-escape -interaction=nonstopmode -halt-on-error presentation.tex
                    '';
                };
            in
            {
                apps.default = {
                    type = "app";
                    program = "${buildReport}/bin/build-frogos-report";
                };

                apps.report = {
                    type = "app";
                    program = "${buildReport}/bin/build-frogos-report";
                };

                apps.presentation = {
                    type = "app";
                    program = "${buildPresentation}/bin/build-frogos-presentation";
                };

                packages.default = buildReport;
                packages.report = buildReport;
                packages.presentation = buildPresentation;

                devShells.default = pkgs.mkShell {
                    packages = buildInputs;
                };
            }
        );
}
