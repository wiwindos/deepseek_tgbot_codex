# Используем официальный Dev Container с Python 3.11
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root

# Установка curl и bash (на всякий случай), а затем Nix
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl bash ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    # Устанавливаем Nix в мультидевлисте режиме (daemon), чтобы flakes работали корректно
    sh <(curl -L https://releases.nixos.org/nix/latest/install) --daemon && \
    # Загружаем nix в этот RUN
    . /root/.nix-profile/etc/profile.d/nix.sh && \
    nix-channel --update && \
    # Включаем экспериментальные flakes
    mkdir -p /etc/nix && \
    echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# Отключаем root и переходим на vscode
USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
