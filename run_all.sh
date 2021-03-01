#! /bin/bash
set -e

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [output directory]"
  exit 1
fi

inputs=(
  "fish 2.5.0"
  "libsequence 1.8.7"
  "mosh 1.2.6"
  "ninja 1.7.2"
#  "opencv 3.2.0"
#  "protobuf 3.3.1"
)

echo "Writing output to folder $1."
mkdir -p $1

for input in "${inputs[@]}"; do
  parts=( $input )
  prog=${parts[0]}
  version=${parts[1]}

  # Flush database to avoid old data
  python manage.py flush --no-input

  echo "Running const-checker on $prog $version."
  scripts/analyze-package.py $prog $version

  outfile="$1/$prog"
  echo "const-checker run complete. Dumping results to $outfile."
  scripts/results.py $prog $version > $outfile
  
done

echo "Done running const-checker! Results are in $1."
