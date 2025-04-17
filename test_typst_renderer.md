# Heading 1

Cupiditate aperiam fugiat debitis et mollitia nemo officia. Explicabo voluptatem et ratione in iste blanditiis expedita in. Quia fugiat consequatur consequatur voluptas. Sequi qui mollitia ipsum voluptas modi. Nostrum animi exercitationem magnam repellendus.

## Subheading 1

Quod voluptatibus odit qui corrupti illo. Eum quibusdam culpa corrupti molestiae tempora praesentium esse. Beatae temporibus suscipit iure eligendi. Et quas iusto nisi. Dolorem ad qui sapiente eum accusamus. Aspernatur dolores ut ut eius suscipit quidem.

> Consequuntur et quae dolores placeat necessitatibus quam. Omnis ea ipsa ea et dolores. Voluptatem rerum reiciendis enim omnis aut. Architecto recusandae ipsam veritatis. Molestias est eum eos. Aut quia praesentium eveniet nostrum et quo eos ratione.

[This is a link](https://neilzone.co.uk).[^1]

[^1]: This is a footnote

Consequatur aut officia deserunt voluptatum autem voluptatem voluptatum neque. Qui vel ut sint unde neque possimus dolorem. A harum doloribus sit facere pariatur adipisci. Tempora voluptates iure sunt rerum ab repudiandae qui. Ut consequatur enim molestiae.

A harum doloribus sit facere pariatur adipisci. Tempora voluptates iure sunt rerum ab repudiandae qui. Ut consequatur enim molestiae. Consequatur aut officia deserunt voluptatum autem voluptatem voluptatum neque. Qui vel ut sint unde neque possimus dolorem.

# Code formatting

I'd run `mdtopdf test_file.md`, for example, and that would put `test_file.pdf` into the same directory.

It uses:

```
/usr/bin/pandoc "$INPUTFILE" --pdf-engine=typst --template=/home/neil/briefcase/Store/typst/decoded.legal.template -o "$PDFFILE"
```

This is before the break.

---

This is after the break.

## A table[^2]

This is a table:

| Column 1      | Column 2      |
| ------------- | ------------- |
| Cell 1, Row 1 | Cell 2, Row 1 |
| Cell 1, Row 2 | Cell 1, Row 2 |

[^2]: another footnote

### Another heading
The following is a list:

- Item A 
- Item B
- Item C

This is a numbered list:

1. Item 1
2. Item 2
3. Item 3

Nested List:

- Item A
  - Item B
    - Item C
- Item D
   * Item E
     1. Item F
     2. Item G
   * Item H
     - Item I
       1. Item J
       2. Item K   

This is _italic_ text. This is **bold** text. This is ~~strikethrough~~ text. This is `inline code` text.

# Heading Level 1
Lorem ip.

## Heading Level 2
Bibby bibby.

Dibby dibby.

### Heading Level 3
ggjhgh 

#### Heading Level 4
yuy iu.

##### Heading Level 5
Level 5 !

###### Heading Level 6
And the last heading at 6!