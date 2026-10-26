```
QUALITY (sorted by avg error, lower is better)
simulated user                interviews  avg error  95% range  persona checks  length ok  words/answer  contradiction caught  errors
-------------------------------------------------------------------------------------------------------------------------------------
deepseek-v4-flash-0731 (off)  5           0.073      0.04-0.12  100%            100%       35.1          67% of 3              0     
deepseek-v4-flash-0731 (low)  5           0.110      0.07-0.15  95%             100%       49.4          100% of 3             0     
nemotron-ultra (off)          5           0.117      0.07-0.17  100%            100%       35.5          33% of 3              0     
deepseek-v4.1-flash (low)     5           0.123      0.10-0.15  100%            100%       36.8          100% of 2             0     
nemotron-3.5-super (off)      5           0.127      0.09-0.16  100%            100%       18.4          33% of 3              0     
deepseek-v4.1-flash (off)     5           0.133      0.10-0.17  85%             100%       44.7          67% of 3              0     
nemotron-3.5-super (low)      5           0.137      0.10-0.17  95%             100%       35.9          67% of 3              0     
nemotron-ultra (low)          5           0.160      0.13-0.20  90%             95%        57.6          67% of 3              0     

COST AND SPEED (full run = projected for the main experiment)
simulated user                $/answer  rate limit  full run $ (users)  full run time
-------------------------------------------------------------------------------------
deepseek-v4-flash-0731 (off)  $0.00009  120/min     $3.36               5.0 h        
deepseek-v4-flash-0731 (low)  $0.00014  120/min     $5.19               5.0 h        
nemotron-ultra (off)          $0.00051  120/min     $18.37              5.0 h        
deepseek-v4.1-flash (low)     $0.00047  120/min     $16.90              5.0 h        
nemotron-3.5-super (off)      $0.00013  120/min     $4.78               5.0 h        
deepseek-v4.1-flash (off)     $0.00027  120/min     $9.85               5.0 h        
nemotron-3.5-super (low)      $0.00035  120/min     $12.53              5.0 h        
nemotron-ultra (low)          $0.00104  120/min     $37.45              5.0 h        

Actual spend for this file: $1.05

Note: 5 test users per model. This is a screening test: when two models' 95% ranges overlap, treat them as tied and decide on cost, speed and valid-JSON rate. Add --repeats 2 or more personas for a firmer answer.
```
