# bash completions for dbcollect
# Permanent activation: create this file as /etc/bash_completion.d/dbcollect.bash

function _dbcollect() {
  local cur prev opts cmd opts1 flags
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  cmd="${COMP_WORDS[1]}"
  opts1="--version --update --cleanup --error"
  opts="--user --filename --days --logons --orahome --nmon --script --skip-sql --skip-cmd --tasks --timeout --include --exclude"
  flags="--debug --quiet --force-awr --strip --no-rac --no-stby --no-awr --no-sar --no-ora --no-sys --no-root --no-acct --no-orainv --no-oratab --no-timeout"
  case $prev in
     --cleanup|--version|--update) ;;
     --error)    COMPREPLY=($(compgen -W "$(dbcollect --error list)" -- $cur)) ;;
     --user)     COMPREPLY=($(compgen -W "root nobody $(ps -ho user -q $(pgrep -d, pmon_))" -- $cur)) ;;
     --tempdir)  COMPREPLY=($(compgen -W "/var/tmp /tmp" -- $cur)) ;;
     --days)     COMPREPLY=($(compgen -W "20 30 90 5" -- $cur)) ;;
     --nmon)     COMPREPLY=($(compgen -o plusdirs -o filenames -f -- $cur)) ;;
     --script)   COMPREPLY=($(compgen -W "$(dbcollect --script list)" -- $cur)) ;;
     --skip-sql) COMPREPLY=($(compgen -W "$(dbcollect --script list)" -- $cur)) ;;
     --include)  COMPREPLY=($(compgen -W "$(ps -eo args | awk -F_ '/^ora_pmon/ {print $NF}')" -- $cur)) ;;
     --exclude)  COMPREPLY=($(compgen -W "$(ps -eo args | awk -F_ '/^ora_pmon/ {print $NF}')" -- $cur)) ;;
     *dbcollect) COMPREPLY=($(compgen -W "$opts1 $opts $flags" -- $cur)) ;;
     *)          COMPREPLY=($(compgen -W "$opts $flags" -- $cur)) ;;
  esac
  return 0
}
complete -F _dbcollect dbcollect

# Activate completions (on bash shell):
# source <(dbcollect --complete)