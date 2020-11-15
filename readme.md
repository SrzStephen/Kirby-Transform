# Kirby Transform
![](https://66.media.tumblr.com/tumblr_lpc46oU6Cy1qi1pnpo1_500.gifv)

> Kirby is an extremely strong circle, and that's all the explanation I need.
## About
Kirby Transform is middleware used to define a common input data format, some common transformational logic and 
some (mostly) self contained classes to help me push data to various data sources which can then be integrated 
into different platforms (eg AWS Lambda, Azure Function, OpenFaaS, K8s Docker containers).
## Motivation
I'm finding that I'm spending a lot of time creating and maintaining IOT Device -> Data Sink pipelines compared 
to creating the devices themselves. 

By ensuring that things will *just work* if I put the data in a common input format, I should be able to build the 
pipeline once and have something reasonably low maintenance, especially if I spend some time upfront writing tests.

## Format
### Top level
Messages are expected to be valid JSON dictionaries
```yaml
collector: String [Required]
    Name of the collection source
data: List of dictonaries [Required]
    The actual data to send. See below for what this looks like.
data_tags: Dict [Optional]
    Dictionary of tags to associate with every data point 
destination: String [Required]
    Initial Destination (EG AWS IOT)
language: String [Required]
    Language the code is written in
messages: List[dict] [Optional]
    List of dictionaries with formatted as dict(fields,tags,timestamp). See the *data* section for more details.
meta_tags: Dict [Optional]
    Dictonary of tags to associate with meta fields 
platform: String [Required]
    Platform the collector is running on (arduino, router etc)
timestamp: Unix Epoch [Optional]
    If missing then this will be treated as when the data was recieved (Which is a really bad workaround).
uptime: Float [Optional]
    Total uptime if this is something continously sending data
version: String [Required]
    Version of the thing sending data

```
### Data
The actual datapoints come in as a list of dictionaries. The naming scheme is basically defined because InfluxDB 
is the first thing that I created this for.
```yaml
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
* Generating a set of data points, and metadata that is useful for tracking/debugging.
* Generating a common output format *#TODO schema validation* to be used down the line to send to specific data sources

## Outputs
Outputs should be (mostly) self contained ways of generating data in a specific format and giving the ability to send 
data to various sources (InfluxDB, Timestream)
* Influx2: Send to InfluxDB version 2.
* Timestream #ToDo: Send to AWS Timestream