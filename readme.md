# Kirby Transform [![Build Status](https://travis-ci.org/SrzStephen/Kirby-Transform.svg?branch=main)](https://travis-ci.org/SrzStephen/Kirby-Transform)
![](https://66.media.tumblr.com/tumblr_lpc46oU6Cy1qi1pnpo1_500.gifv)

> Kirby is an extremely strong circle, and that's all the explanation I need.

## About
Kirby Transform is middleware used to define a common data format and transformation logic to make it easier for me to
build IOT pipelines. This transformation logic is split into:

### Preprocessor
The preprocessor is responsible for:
* Input validation
* Generating a set of data points, and metadata that is useful for tracking/debugging.
* Generating a common output format to be used down the line to send to specific data sources.

### Outputs
Outputs should be (mostly) self contained ways of generating data in the required format and sending data to 
storage solutions.

#### Currently Implemented:
- InfluxDB2
- AWS Timestream


## Motivation
I'm finding that I'm spending a lot of time creating and maintaining IOT Device -> Data Sink pipelines compared 
to creating the devices themselves. 

By ensuring that things will *just work* if I put the data in a common input format, I should be able to build the 
pipeline once and have something reasonably low maintenance.

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

### Examples
The best place to look for examples is in the ```tests``` folder. There are examples of data and how to use, 
wrapped up as test cases.

### Structure
As this is middleware for very inter related projects, this how I'm expecting to structure the project:
* This package is uploaded to PiPi
* Things that depend on this package (Eg Lambdas) should be put in their own repo, being submoduled to this one to make 
testing everything significantly easier.
* Dependent packages should be pinned to a specific Kirby Transform version, and should be updated as needed.

