# Kirby Transform
![](https://66.media.tumblr.com/tumblr_lpc46oU6Cy1qi1pnpo1_500.gifv)
Middleware to define a common format for my IOT projects so that I can easily push to various sources without making changes.

## Format
### Top level
Messages are expected to be valid JSON dictionaries
```yaml
collector: String [Required]
    Name of the collection source
data: List of dictonaries [Required]
    The actual data to send. See below for what this looks like.
data_tags: Dictionary of tags to associate with every data point [Optional]
destination: Initial Destination [Required]
language: String [Required]
    Language the code is written in
messages: [Optional]
meta_tags: Dictonary of tags to associate with meta fields [Optional]
platform: String [Required]
    Platform the collector is running on (arduino, router etc)
timestamp: Unix Epoch [Optional]
    If missing then this will be treated as when the data was recieved (Which is a really bad workaround).
uptime: Float [Optional]
version: String [Required]

```
### Data
the actual datapoints come in as a list of dictionaries
```docs
tags: Dictionary [Optional]
    Dictonary of tags to add to individual datapoints
fields: Dictonary [Required]
    Datapoint fields.
timestamp: Unix Epoch [Optional]
    Timestamp for the data (Resolution in seconds).  If this is missing then the report timestamp will be used
```
## Preprocessor
The preprocessor is responsible for:
* Input validation
* Generating output format
* Puttin
* Generating an output similar to the expected data output for




```docs
{
"meta":
{
tags
fields
timestamp
}

"data":
tags
fields
timestamp
```


## Outputs
Outputs should be (mostly) self contained ways of generating data in a specific format and giving the ability to send it to various sources (InfluxDB, Timestream)