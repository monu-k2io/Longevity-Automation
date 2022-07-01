# Longevity Automation

## Using this script you can run longevity for below-mentioned agents:
- NodeJS
- PHP
- Python
- Java

## Usage
```bash
python3 start_longevity.py -l <AGENT>
```

> #### OPTIONS:
> `-l/--language <argument>` Start longevity for specified language
> 
	> 		Valid argument with -l are:
	> 			node - to start longevity for Node agent
	> 			python - to start longevity for Python agent
	> 			java - to start longevity for Java agent
	> 			php - to start longevity for PHP agent
	> 			all - to start longevity for all mentioned agents
> 
> `-c/--clean <argument>` Clean longevity setup for specified language
> 
	> 		Valid argument with -c are:
	> 			node - to clean longevity setup for Node agent
	> 			python - to clean longevity setup for Python agent
	> 			java - to clean longevity setup for Java agent
	> 			php - to clean longevity setup for PHP agent
	> 			all - to clean longevity setup for all mentioned agents