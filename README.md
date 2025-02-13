![alt text](assets/save-the-data-header.png)

# Save The Data 

A fork of [UI-Research/data-preservation-public](https://github.com/UI-Research/data-preservation-public)

## Partnering Organizations (alphabetical order)
(list as of February 12, 2025)

- [American Educational Research Association](https://www.aera.net/)
- [Georgetown University Ethics Lab](https://ethicslab.georgetown.edu/)
- [Georgetown University Department of Sociology](https://sociology.georgetown.edu/)
- [Georgetown University Department of Computer Science](https://cs.georgetown.edu/)
- [Georgetown University Library](https://library.georgetown.edu/)
- [Massive Data Institute](https://library.georgetown.edu/scholarly-communication)
- [University of Michigan Institute for Social Research](https://isr.umich.edu/)
- [Urban Institute](https://www.urban.org/)


## Technical Guidance

[Follow Urban Institute's README](README_UI.md)

### Saving

GCP Bucket for saving: https://console.cloud.google.com/storage/browser/save_the_data

1. copy the `json.key` from the `resources` folder in the bucket

2. update the constants in the [save_to_bucket script](output/save_to_bucket.py) to point to your local files as directed.

2. Run the script

```py
python -m output.save_to_bucket
```
3. check your data in the bucket listed above