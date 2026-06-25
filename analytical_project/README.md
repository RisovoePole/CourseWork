# Tests

**recursive**:

``` bash
python_app  | ----ultra_easy-----
python_app  | run_parallel: 0.069 s
python_app  | run_backtracking: 0.002 s
python_app  | ----very_easy-----
python_app  | run_parallel: 1.050 s
python_app  | run_backtracking: 2.229 s
python_app  | ----medium-----
python_app  | run_parallel: 64.246 s
python_app  | run_backtracking: 162.009 s
python_app  | .
python_app  | ----------------------------------------------------------------------
python_app  | Ran 1 test in 229.635s
python_app  | 
python_app  | OK
```

**iterative**:

```bash
python_app  | ----ultra_easy-----
python_app  | run_parallel: 0.069 s
python_app  | run_backtracking: 0.002 s
python_app  | ----very_easy-----
python_app  | run_parallel: 1.013 s
python_app  | run_backtracking: 1.780 s
python_app  | ----medium-----
python_app  | run_parallel: 59.587 s
python_app  | run_backtracking: 130.856 s
python_app  | .
python_app  | ----------------------------------------------------------------------
python_app  | Ran 1 test in 193.337s
python_app  | 
python_app  | OK
```