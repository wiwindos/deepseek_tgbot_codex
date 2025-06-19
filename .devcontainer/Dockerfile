# .devcontainer/Dockerfile
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root
SHELL ["/bin/bash", "-lc"]

# 1) Системные утилиты
RUN apt-get update \
 && apt-get install -y curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Подготовка /nix и группы build-пользователей
RUN mkdir -m 0755 /nix \
 && groupadd --system nixbld \
 && useradd --system --no-create-home --shell /usr/sbin/nologin --gid nixbld nixbld1

# 3) Установим Nix под vscode-пользователем
USER vscode
ENV HOME=/home/vscode
ENV USER=vscode
SHELL ["/bin/bash", "-lc"]

RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --no-daemon \
 && rm /tmp/install-nix.sh

# 4) Конфигурируем flakes и экспортируем PATH
RUN mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" | sudo tee /etc/nix/nix.conf

ENV PATH=/home/vscode/.nix-profile/bin:/home/vscode/.nix-profile/sbin:${PATH}

# Окончательно: отрабатываем как vscode
USER vscode
