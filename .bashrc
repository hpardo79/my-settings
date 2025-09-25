# ~/.bashrc - Configuración optimizada y unificada
# ==================================================

# Salir si no es shell interactiva
case $- in
    *i*) ;;
      *) return;;
esac

# ================================
# Historial
# ================================
HISTCONTROL=ignoredups:erasedups
HISTSIZE=10000
HISTFILESIZE=20000
HISTTIMEFORMAT="%F %T "

# Sincronizar historial en tiempo real entre sesiones
PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

# ================================
# Opciones útiles de Bash
# ================================
shopt -s histappend
shopt -s checkwinsize
shopt -s globstar

# ================================
# lesspipe para archivos no-texto
# ================================
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# ================================
# Prompt (Powerline + Git optimizado)
# ================================
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# Cargar git-prompt (más eficiente que parse_git_branch)
if [ -f /usr/share/git/completion/git-prompt.sh ]; then
    . /usr/share/git/completion/git-prompt.sh
    GIT_PS1_SHOWDIRTYSTATE=1
    GIT_PS1_SHOWCOLORHINTS=1
fi

# Construcción del prompt
build_prompt() {
  local user_host="\[\e[30;42m\] \u│\h \[\e[0m\]"
  local sep1="\[\e[30;42m\]░▒▓\[\e[0m\]"
  local directory=" \[\e[1;32m\]\w\[\e[0m\]"

  PS1="${user_host}${sep1}${directory}"

  # Agregar Git si aplica
  if type __git_ps1 &>/dev/null; then
      local git_block="\[\e[0m\]\[\e[97;104m\]$(__git_ps1 ' %s ')\[\e[0m\]"
      PS1+="$git_block"
  fi

  PS1+=" \[\e[1;32m\]\$ \[\e[0m\]"
}
PROMPT_COMMAND=build_prompt

# Título de ventana en xterm
case "$TERM" in
xterm*|rxvt*) 
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u│\h: \w\a\]$PS1"
    ;;
*) ;;
esac

# ================================
# Colores y alias
# ================================
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto -n'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Aliases útiles
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ports='netstat -tulanp'

# Alias seguros
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Alertas de comandos largos
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" \
"$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# ================================
# Bash completion
# ================================
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# ================================
# Funciones
# ================================
mkcd () { mkdir -p "$1" && cd "$1"; }

extract () {
    if [ -f "$1" ] ; then
        case "$1" in
            *.tar.bz2)   tar xvjf "$1" ;;
            *.tar.gz)    tar xvzf "$1" ;;
            *.bz2)       bunzip2 "$1" ;;
            *.rar)       unrar x "$1" ;;
            *.gz)        gunzip "$1" ;;
            *.tar)       tar xvf "$1" ;;
            *.tbz2)      tar xvjf "$1" ;;
            *.tgz)       tar xvzf "$1" ;;
            *.zip)       unzip "$1" ;;
            *.Z)         uncompress "$1" ;;
            *.7z)        7z x "$1" ;;
            *.xz)        unxz "$1" ;;
            *.tar.xz)    tar xvJf "$1" ;;
            *)           echo "No sé cómo extraer '$1'..." ;;
        esac
    else
        echo "'$1' no es un archivo válido"
    fi
}

# ================================
# Historial inteligente con Readline
# ================================

# Hace que ↑ y ↓ busquen en el historial solo lo que empieza con lo ya escrito
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Opcional: Ctrl+F para autocompletar con la última coincidencia del historial
_suggest_from_history() {
    local curr=${READLINE_LINE:0:READLINE_POINT}
    local match=$(history | grep -F "$curr" | tail -n1 | sed 's/ *[0-9]\+ *//')
    if [[ -n "$match" ]]; then
        READLINE_LINE=$match
        READLINE_POINT=${#match}
    fi
}
bind -x '"\C-f": _suggest_from_history'

# ================================
# Integraciones externas
# ================================
command -v zoxide &>/dev/null && eval "$(zoxide init bash)"

