set INTERVAL=3600
:Again  
taskkill /f /im ga* 
for /l %%x in (1, 1, 8) do start /min "" game.exe battle %%x 101 102 103 104 106 101 102 103 104 106 spd 4
timeout %INTERVAL%
goto Again  
