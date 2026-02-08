# ── Cool Terminal Setup ──────────────────────────────────────

# Starship prompt
eval "$(starship init bash)"

# Modern aliases
alias ls='eza --icons --group-directories-first'
alias ll='eza -la --icons --group-directories-first --git'
alias lt='eza --tree --icons --level=2'
alias la='eza -a --icons --group-directories-first'
alias cat='batcat --style=auto'
alias bat='batcat'

# Git shortcuts
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline --graph --decorate -20'
alias gp='git pull'
alias gfix='git add . && git commit -m "fix" && git push'

# Colored grep
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# Better defaults
export BAT_THEME="Dracula"
export EDITOR="code --wait"
