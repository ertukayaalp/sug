PYTHONPATH=$(pwd):$PYTHONPATH\
  $VIRTUAL_ENV/bin/python3.3 -m unittest tests/test_*.py $@
