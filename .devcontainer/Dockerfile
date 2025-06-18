FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# Установка Nix
RUN curl -L https://releases.nixos.org/nix/latest/install | sh \
  && . /root/.nix-profile/etc/profile.d/nix.sh \
  && nix-channel --update

# Включаем поддержку flakes
RUN . /root/.nix-profile/etc/profile.d/nix.sh \
  && mkdir -p /etc/nix \
  && echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf
