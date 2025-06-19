FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root

# Чтобы Bash подхватывал profile-скрипты и экспорт PATH
SHELL ["/bin/bash", "-lc"]

# Системные утилиты
RUN apt-get update \
 && apt-get install -y curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Установка Nix (single-user mode проще в контейнере)
RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --no-daemon \
 && . /root/.nix-profile/etc/profile.d/nix.sh \
 && mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf \
 && rm /tmp/install-nix.sh

# Всегда доступен nix
ENV PATH=/root/.nix-profile/bin:/root/.nix-profile/sbin:${PATH}

USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
