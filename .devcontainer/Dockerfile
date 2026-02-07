FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    sudo \
    apt-transport-https \
    ca-certificates \
    gnupg \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y --no-install-recommends google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# Install terminal tools (starship, eza, bat, nerd font)
RUN apt-get update && apt-get install -y --no-install-recommends \
    eza bat unzip fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sS https://starship.rs/install.sh | sh -s -- -y

# Install FiraCode Nerd Font
RUN mkdir -p /usr/local/share/fonts \
    && curl -fLo /tmp/FiraCode.zip https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FiraCode.zip \
    && unzip -o /tmp/FiraCode.zip -d /tmp/FiraCode_NF \
    && cp /tmp/FiraCode_NF/*.ttf /usr/local/share/fonts/ \
    && fc-cache -fv \
    && rm -rf /tmp/FiraCode.zip /tmp/FiraCode_NF

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Terminal customization for vscode user
COPY .devcontainer/starship.toml /home/$USERNAME/.config/starship.toml
COPY .devcontainer/terminal-setup.sh /home/$USERNAME/.terminal-setup.sh
RUN echo '\n# Load terminal customization\n[ -f ~/.terminal-setup.sh ] && . ~/.terminal-setup.sh' >> /home/$USERNAME/.bashrc \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME/.config /home/$USERNAME/.terminal-setup.sh

USER $USERNAME
