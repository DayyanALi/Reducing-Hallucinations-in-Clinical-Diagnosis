#!/bin/bash

echo "Making /mnt/e/detectionAG/output/mixed_audio directory..."
mkdir -p "/mnt/e/detectionAG/output/mixed_audio"

echo "Mixing audio..."
for f in /mnt/e/detectionAG/audios/*_doctor.wav
do
  [[ -e "$f" ]] || break
  base=$(basename "$f" "_doctor.wav")
  patient_file="/mnt/e/detectionAG/audios/${base}_patient.wav"
  outputpath="/mnt/e/detectionAG/output/mixed_audio/${base}.wav"

  echo "------------------------------------"
  echo "Doctor file   : $f"
  echo "Base name     : $base"
  echo "Patient file  : $patient_file"
  echo "Output file   : $outputpath"

  if [[ -f "$patient_file" ]]; then
    echo "Running sox..."
    sox -m "$f" "$patient_file" "$outputpath"
    echo "✅ Mixed: $outputpath"
  else
    echo "❌ Skipping $f (no matching patient file found)"
  fi
done

echo "Done!"
