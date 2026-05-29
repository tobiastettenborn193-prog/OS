source /usr/share/cachyos-zsh-config/cachyos-config.zsh

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# Created by `pipx` on 2026-04-28 22:02:18
export PATH="$PATH:/home/tobster/.local/bin"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.local/npm-global/bin:$PATH"

alias sounddriver-restart='systemctl --user restart pipewire pipewire-pulse wireplumber'
alias aliasconf='sudo nano ~/.zshrc'
alias fastf ='fastfetch'
alias pacinstall='sudo pacman -S'
alias flatinstall='sudo flatpak install'
alias pacuninstall='sudo pacman -R'
alias flatuninstall='sudo flatpak uninstall'
alias listalias='cd /home/tobster/Projekte/alias_list/list_alias/src && cargo run && cd .. && cd .. && cd .. && cd ..'

alias sr='systemctl --user restart pipewire pipewire-pulse wireplumber'
alias sd='shutdown'


alias math='noglob _calc'
alias mathf='noglob _calcf'

_calc() {
  python3 -c "
import re
from math import *
expr = '$*'
expr = re.sub(r'(?<=\d) (?=\d)', '', expr)
expr = expr.replace('sq(', 'sqrt(')
result = eval(expr)
if isinstance(result, float) and result == int(result):
    result = int(result)
if isinstance(result, int):
    formatted = '{:,}'.format(result).replace(',', ' ')
else:
    integer, decimal = '{:,.2f}'.format(result).split('.')
    formatted = integer.replace(',', ' ') + '.' + decimal
print(formatted)
"
}


_calcf() {
  python3 -c "
import re
from math import *
expr = '$*'
expr = re.sub(r'(?<=\d) (?=\d)', '', expr)
expr = expr.replace('sq(', 'sqrt(')
suffixes = [
    ('sx', 1_000_000_000_000_000_000),
    ('qu', 1_000_000_000_000_000),
    ('qt', 1_000_000_000_000),
    ('b',  1_000_000_000),
    ('m',  1_000_000),
    ('k',  1_000),
    ('t',  1_000_000_000_000),
]
for suffix, multiplier in suffixes:
    expr = re.sub(r'(\d+(?:\.\d+)?)' + suffix, lambda m, x=multiplier: str(float(m.group(1)) * x), expr, flags=re.IGNORECASE)
result = eval(expr)
if isinstance(result, float) and result == int(result):
    result = int(result)
abs_result = abs(result)

if abs_result >= 1_000_000_000_000_000_000:
    formatted = f'{result / 1_000_000_000_000_000_000:.2f}'.rstrip('0').rstrip('.') + 'Sx'
elif abs_result >= 1_000_000_000_000_000:
    formatted = f'{result / 1_000_000_000_000_000:.2f}'.rstrip('0').rstrip('.') + 'Qu'
elif abs_result >= 1_000_000_000_000:
    formatted = f'{result / 1_000_000_000_000:.2f}'.rstrip('0').rstrip('.') + 'T'
elif abs_result >= 1_000_000_000:
    formatted = f'{result / 1_000_000_000:.2f}'.rstrip('0').rstrip('.') + 'B'
elif abs_result >= 1_000_000:
    formatted = f'{result / 1_000_000:.2f}'.rstrip('0').rstrip('.') + 'M'
elif abs_result >= 1_000:
    formatted = f'{result / 1_000:.2f}'.rstrip('0').rstrip('.') + 'k'
else:
    formatted = str(result)
print(formatted)
"
}