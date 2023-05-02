# incentive-processor
Human-in-the-loop automation of incentive payment verification and EOB download

### Steps:
1. {HUMAN} Upload deidentified Epic export (`csv` or `.xlsx`) & Experian "Remittance Detail CalOptima Incentives" `csv`
2. {AUTOMATED} Script will verify which reference numbers in the Epic export are Caloptima incentives
  * script will notify if any Experian items are **not** in Epic export (i.e. missing 835 in Epic)
  * script will output comma-separated list of reference numbers
3. {HUMAN} Open "Remittance Detail Report" >> make sure date filter is set to "Current Day" >> paste output of verified reference numbers into the "Remittance Numbers" field >> Click "PDF" button
4. {HUMAN} Upload resulting PDF >> click "Split"
5. {AUTOMATED} Use `PyPDF2` to split PDF at each change of "Remittance #" (page header) >> name each file according to the NPI listed (i.e. name lookup by NPI) >> returns zipfile of all incentive EOB PDF's
6. {HUMAN} download zipfile >> extract >> put all EOB's in correct netowrk folder
