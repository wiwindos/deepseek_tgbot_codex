# .devcontainer/Dockerfile

FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root

# 1) Системные утилиты
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Установка Nix (официальный скрипт)
RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --daemon \
 && . /root/.nix-profile/etc/profile.d/nix.sh \
 && nix-channel --update \
 && mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf \
 && rm /tmp/install-nix.sh

# 3) Возврат под vscode и добавление nix в PATH
USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
