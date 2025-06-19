# .devcontainer/Dockerfile
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root
SHELL ["/bin/bash", "-lc"]

# 1) Системные утилиты
RUN apt-get update \
 && apt-get install -y curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Создаём группу и одного пользователя для nixbld
RUN groupadd --system nixbld \
 && useradd --system --gid nixbld nixbld1

# 3) Установка Nix в однопользовательском режиме
RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --no-daemon \
 && . /root/.nix-profile/etc/profile.d/nix.sh \
 && mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf \
 && rm /tmp/install-nix.sh

# 4) Добавляем nix в PATH
ENV PATH=/root/.nix-profile/bin:/root/.nix-profile/sbin:${PATH}

USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
