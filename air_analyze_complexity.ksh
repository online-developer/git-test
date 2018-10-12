#!/bin/ksh

filename="complexity.txt"
[[ -f "$filename" ]] && rm -f "$filename"
touch "$filename"

for project in $(air category list-members -m project); do
   root=$(echo $project | awk -F '/' '{print $2}' )
   if [[ "$root" == "Projects" ]]; then
      echo "$project"
      air project analyze-dependencies "$project" -all -complexity-details -verbose >> "$filename"
   fi
done

