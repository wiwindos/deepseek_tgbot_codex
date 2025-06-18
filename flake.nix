{
  description = "DeepSeek Telegram bot with reproducible dev shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";

  outputs = { self, nixpkgs }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    devShells.default = pkgs.mkShell {
      packages = with pkgs; [
        python311 python311Packages.poetry python311Packages.pytest
        python311Packages.aiogram
        python311Packages.pytest_httpx python311Packages.pytest_asyncio python311Packages.aiogram_mock
        sqlite git
      ];
      SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
    };
  };
}
