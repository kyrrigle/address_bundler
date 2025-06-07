# Functional Specification: Signs image validation

## Overview

Validate original photos to meet specific constraints:

- Readable image file (supported types: jpeg, png)
- Minimum resolution in total pixels (configurable in project. default 1000000)

Using the command line

```
    ab-signs validate
```

Student records in the database should have an `image_valid` property that can be `unkonwn`, `valid` or `invalid`.   This command will update the property.


## Functional Requirements

### 1. Inputs

The images within the `<project>/outputs/` directory corresponding to students in the database

### 2. Outputs

For each photo that isn't valid report to standard output the student's name, the file name and the reason why.

Once validated, the student record should be marked to say that it is valid. 

### 3. Constraints

- Importing a new photo for a student (image file is different) should remove the validity flag on the database record (set it to `unknown`


## Notes

- Code should be modular and testable
- Create test cases as you go
