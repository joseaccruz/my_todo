rm output.txt
rm result.txt

# error conditions
coverage run ../todo.py -t -p empty >> output.txt
coverage run -a ../todo.py -t -p errors/errors1.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors2.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors3.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors4.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors5.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors6.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors7.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors8.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors9.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors10.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors11.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors11.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/errors12.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/test_empty1.todo >> output.txt 2> /dev/null
coverage run -a ../todo.py -t -p errors/test_empty2.todo >> output.txt 2> /dev/null

# error in date
coverage run -a ../todo.py -d xpto -t -p ok >> output.txt 2> /dev/null


# normal conditions
echo -e "\n\n--- default ---" >> result.txt
coverage run -a ../todo.py -d 2024-06-01 -t -p ok >> result.txt

coverage run -a ../todo.py -d 2024-06-01 -t -p ok/test0.todo >> result.txt

echo -e "\n\n--- mini ---" >> result.txt
coverage run -a ../todo.py -d 2024-06-01 -t -p ok mini >> result.txt

echo -e "\n\n--- all ---" >> result.txt
coverage run -a ../todo.py -d 2024-06-01 -t -p ok all >> result.txt

# for coverage of the report module
coverage run -a ../todo.py -d 2024-06-01 -p ok all >> output.txt
coverage run -a ../todo.py -d 2024-06-01 -p empty >> output.txt

# for coverage of the load data
coverage run -a ../todo.py -d 2030-04-30 -p ok all >> output.txt

# for coverage of the relative date computation
# we don't keep the output in 'result.txt' because it depends on the
# running date and thus are unpredictable.
coverage run -a ../todo.py -d +2d -p ok mini > /dev/null
coverage run -a ../todo.py -d +2w -p ok mini > /dev/null
coverage run -a ../todo.py -d +2m -p ok mini > /dev/null


coverage html

diff result.txt expected_result.txt
diff output.txt expected_output.txt
