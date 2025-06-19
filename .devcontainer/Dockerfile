# .devcontainer/Dockerfile
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root
SHELL ["/bin/bash", "-lc"]

# 1) Системные утилиты
RUN apt-get update \
 && apt-get install -y curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Создаём группу и пользователя, и явно вносим его в список группы
RUN groupadd --system nixbld \
 && useradd --system --no-create-home --shell /usr/sbin/nologin nixbld1 \
 && gpasswd -a nixbld1 nixbld

# 3) Установка Nix в однопользовательском режиме
RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --no-daemon \
 && . /root/.nix-profile/etc/profile.d/nix.sh \
 && mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf \
 && rm /tmp/install-nix.sh

# 4) Добавляем nix в PATH для всех последующих команд
ENV PATH=/root/.nix-profile/bin:/root/.nix-profile/sbin:${PATH}

# Возвращаемся к non-root пользователю vscode
USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
