```
QUALITY (sorted by avg error, lower is better)
interviewer                interviews  avg error  95% range  band exact  within 1  valid JSON  mismatch caught  contradiction caught  false contra/interview  questions  errors
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
kimi-k3 (low)              5           0.107      0.08-0.13  40%         100%      100%        100%             0% of 3               0.0                     10.0       0     
glm-5.3 (low)              5           0.110      0.08-0.14  60%         100%      100%        100%             0% of 3               0.3                     9.8        0     
beam (low)                 5           0.110      0.06-0.16  80%         100%      100%        100%             33% of 3              0.0                     9.6        0     
nemotron-ultra (low)       5           0.147      0.08-0.21  60%         100%      100%        100%             0% of 3               0.0                     8.8        0     
muse-spark-open (low)      5           0.147      0.09-0.22  80%         80%       100%        100%             67% of 3              0.0                     9.2        0     
deepseek-v4.1-flash (low)  5           0.148      0.11-0.20  60%         80%       100%        100%             67% of 3              0.7                     9.0        0     

COST AND SPEED (full run = projected for the main experiment)
interviewer                $/interview  output tokens  thinking tokens  secs/interview  rate limit  full run $  full run time
-----------------------------------------------------------------------------------------------------------------------------
kimi-k3 (low)              $0.074       1851           607              214.9           15/min      $133.95     22.0 h       
glm-5.3 (low)              $0.024       1394           189              229.9           120/min     $43.22      2.7 h        
beam (low)                 $0.010       3783           2561             200.1           15/min      $17.58      21.2 h       
nemotron-ultra (low)       $0.014       3037           1968             216.0           120/min     $25.11      2.5 h        
muse-spark-open (low)      $0.026       2300           1173             211.6           120/min     $46.53      2.5 h        
deepseek-v4.1-flash (low)  $0.008       3690           2657             206.6           120/min     $14.21      2.5 h        

Actual spend for this file: $0.81

Note: 5 test users per model. This is a screening test: when two models' 95% ranges overlap, treat them as tied and decide on cost, speed and valid-JSON rate. Add --repeats 2 or more personas for a firmer answer.
```
