{
  description = "DeepSeek Telegram bot – reproducible dev shell";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.default = pkgs.mkShell {
        # ► только инструменты, которые реально нужны из Nix
        buildInputs = with pkgs; [
          python311        # интерпретатор
          poetry           # менеджер зависимостей / виртуалка
          sqlite           # бинарь sqlite3 (если нужен миграциям)
          git
        ];

        # чтобы requests/poetry видели корневые сертификаты
        SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";

        # автоматически поднимаем venv + зависимости
        shellHook = ''
          if [ ! -d .venv ]; then
            poetry install
          fi
        '';
      };
    });
}
