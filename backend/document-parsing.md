# Document parsing

## What is document parsing?

Document parsing is a process of automatically converting any document to structured text such as HTML or Markdown.
It detects layout elements such as paragraphs, tables, images, and more to determine the structure of the document.
The API then serializes the elements according to reading order, and finally converts the document into structured text.

## What models does Upstage provide?

The table below lists models currently available as an API. Upstage provides stable *aliases*aliases that point to specific model versions, allowing you to integrate once and automatically benefit from future updates. We recommend using aliases instead of hardcoding model names, as models can be frequently updated.

| Alias | Currently points to | RPS (Learn more) |
| --- | --- | --- |
|  | document-parse-250618 | 10 (Sync) / 30 (Async) |
|  | document-parse-250508 | 10 (Sync) / 30 (Async) |
| document-parse | document-parse-250404 | 10 (Sync) / 30 (Async) |

## Input requirements

- Supported file formats: JPEG, PNG, BMP, PDF, TIFF, HEIC, DOCX, PPTX, XLSX, HWP, HWPX

- Maximum file size: 50MB

- Maximum number of pages per file:   - Synchronous API: 100 pages (For files exceeding 100 pages, the first 100 pages are processed)   - Asynchronous API: 1,000 pages

- Maximum pixels per page: 200,000,000 pixels. (For non-image files, the number of pixels is determined after converting the document to images at 150 DPI.)

- Supported character sets (if using OCR): Alphanumeric, Hangul, and Hanja are supported. Hanzi and Kanji are in beta versions, which means they are available but not fully supported.

Hanja, Hanzi, and Kanji are writing systems based on Chinese characters used in Korean, Chinese, and Japanese writing systems. Despite sharing similarities, they possess distinct visual representations, pronunciations, meanings, and usage conventions within their respective linguistic contexts. For more information, see [this article](https://en.wikipedia.org/wiki/Hanja)this article.

For best results, follow these guidelines:

- Use high-resolution documents to ensure legibility of text.

- Ensure a minimum document width of 640 pixels.

- The performance of the model might vary depending on the text size. Ensure that the smallest text in the image is at least 2.5% of the image's height. For example, if the image is 640 pixels tall, the smallest text should be at least 16 pixels tall.

## Understanding the outputs

### Layout categories and HTML tags

Upstage Document Parse identifies various *layout categories*layout categories in the input document and converts them to *HTML tags*HTML tags.

The table below describes all layout categories and corresponding HTML tags.
If there is no suitable HTML tag for the layout category, it uses a `<p>`<p> tag with a `data-category`data-category attribute to explain the layout category detected by the model.

| Layout category | HTML tag |
| --- | --- |
| table | <table> .. </table> |
| figure | <figure><img> .. </img></figure> |
| chart | <figure><img data-category="chart"> .. </img></figure> |
| heading1 | <h1>... </h1> |
| header | <header> .. </header> |
| footer | <footer> .. </footer> |
| caption | <caption> .. </caption> |
| paragraph | <p data-category="paragraph">..</p> |
| equation | <p data-category="equation">..</p> |
| list | <p data-category="list">..</p> |
| index | <p data-category="index">..</p> |
| footnote | <p data-category="footnote"> </p> |

A detailed example of layout categories can be seen in the example below.

### Chart recognition

Although charts within documents contain useful information, they are normally parsed as images, making it difficult to utilize them for tasks such as search, QA, or RAG.
Extracting numerical data from charts into tables allows seamless integration into existing text-based pipelines, enabling the effective utilization of chart information.
While one could use a multi-modal LLM to address this issue, it tends to be more expensive and leads to a more complex pipeline compared to text-based LLMs.

With the chart recognition feature in Upstage Document Parse, the following chart types are recognized and converted into a table format.

- Bar charts

- Line charts

- Pie charts

The following is an example.

**Chart input**Chart input

**HTML output**HTML output

```
<figure id='2' data-category='chart'>
  <img data-coord="top-left:(118,157); bottom-right:(900,393)" />
  <figcaption>
    <p>Chart Title: FMD VACCINATION COVERAGE IN SELECTED ZONE 2 EXTENTION AREAS DURING THE OCTOBER 2014 TUBU FMD OUTBREAK</p>
    <p>X-Axis: EXTENTION AREAS</p>
    <p>Y-Axis: Cumulative % Coverage</p>
    <p>Chart Type: bar</p>
  </figcaption>
  <table>
    <tr>
      <th></th>
      <th>TUBU</th>
      <th>NOKANENG</th>
      <th>HABU</th>
      <th>ETSHA 6</th>
      <th>GUMARE</th>
      <th>TSAU</th>
    </tr>
    <tr>
      <td>item_01</td>
      <td>79%</td>
      <td>90%</td>
      <td>71%</td>
      <td>69%</td>
      <td>77%</td>
      <td>37%</td>
    </tr>
  </table>
</figure>
```

- <img> : Coordination information for the chart

- <figcaption> : Chart metadata, with each item separated by a <p> tag   1. Chart title (Optional): The title of the chart   2. X-axis (Optional): The x-axis label   3. Y-axis (Optional): The y-axis label   4. Chart type: Identified as bar, line, or pie chart

- <table> : The recognized chart data in table format

Under the hood, confidence scores for chart recognition are calculated for each chart.
If chart recognition is successful according to the confidence score,
the chart is categorized as a `chart`chart and the resulting table is displayed in HTML.
If recognition fails, the chart is categorized as a `figure`figure and the response contains HTML, Markdown and text.

**If chart recognition succeeds → "Chart"**If chart recognition succeeds → "Chart"

```
{
  "category": "chart",
  "content": {
    "html": "<figure id='4' data-category='chart'><img data-coord=\"top-left:(175,1305); bottom-right:(785,1784)\" /><figcaption><p>Chart Type: bar</p></figcaption><table><tr><th></th><th>Nuclear</th><th>Renewables</th><th>Hydro</th><th>Natural gas</th><th>Coal</th><th>Oil</th></tr><tr><td>item_01</td><td>4%</td><td>4%</td><td>7%</td><td>24%</td><td>27%</td><td>34%</td></tr></table></figure>",
    "markdown": "- Chart Type: bar\n|  | Nuclear | Renewables | Hydro | Natural gas | Coal | Oil |\n| --- | --- | --- | --- | --- | --- | --- |\n| item_01 | 4% | 4% | 7% | 24% | 27% | 34% |\n",
    "text": "Chart Type: bar \nNuclear Renewables HydroNatural gas Coal Oil\n item_01 4% 4% 7% 24% 27% 34%"
  },
  "id": 4,
  "page": 1
}
```

- html : <figcaption> and <table> elements are added inside the <figure data-category='chart'> tag

- markdown : The result in Markdown format

- text : The result in raw text

**If chart recognition fails → "Figure"**If chart recognition fails → "Figure"

```
{
  "category": "figure",
  "content": {
    "html": "<figure id='4' data-category='chart'><img style='font-size:20px' alt=\"Nuclear 4%\nRenewables 4%\nHydro 7%\nNatural gas 24%\nCoal 27%\nOil 34%\" data-coord=\"top-left:(175,1306); bottom-right:(785,1783)\" /></figure>",
    "markdown": "Nuclear 4%\nRenewables 4%\nHydro 7%\nNatural gas 24%\nCoal 27%\nOil 34%",
    "text": "Nuclear 4%\nRenewables 4%\nHydro 7%\nNatural gas 24%\nCoal 27%\nOil 34%"
  },
  "id": 4,
  "page": 1
}
```

- html : The OCR result is added to the alt attribute of the <img> tag within <figure data-category='chart'>

- markdown : The OCR result

- content : The OCR result

### Equation recognition

For the `equation`equation category output, the model provides recognized text in [LaTex format](https://en.wikibooks.org/wiki/LaTeX/Mathematics)LaTex format within the `<p data-category="equation">`<p data-category="equation"> tag to ensure proper display using popular equation rendering engines like [MathJax](https://www.mathjax.org/)MathJax.
The output of a sample equation image can be seen below.

```
{
  "category": "equation",
  "content": {
      "html": "<p id='3' data-category='equation'>$$a_{n}=\\sum_{k=1}^{n}{\\frac{2k+1}{\\,1^{2}+2^{2}+3^{2}+\\cdots+k^{2}}}$$</p>",
      "markdown": "$$a_{n}=\\sum_{k=1}^{n}{\\frac{2k+1}{\\,1^{2}+2^{2}+3^{2}+\\cdots+k^{2}}}$$,
      "text": "n 2k+1 \nan  \nk=1 12+22+32 + · · +k2"
  },
}
```

In the response, the `content.html`content.html and `content.markdown`content.markdown fields contain the recognized equation in LaTex format, while the `content.text`content.text field contains the OCR result text.
Because the OCR model does not support equation recognition at the moment, the `content.text`content.text field may not contain the correct equation text. For equation category, the OCR result in the `content.text`content.text field is provided for backward compatibility.

Users may have difficulty rendering the `content.html`content.html field value properly in their HTML file.
This is because the API response in JSON format escapes the `\`\ character. To resolve this issue, they can use JavaScript to unescape the HTML.
The example code below demonstrates how to render the equation properly in an HTML file by importing the MathJax library and unescaping the API response.

```
<body>
    <div id="equation" /> <!-- placeholder for equation -->
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script type="text/javascript">
        <!-- put the API response to innerHTML field -->
        document.getElementById('equation').innerHTML = "<p id='5' data-category='equation'>$$f(x)=a_{0}+\\sum_{n=1}^{\\infty}\\left(a_{n}\\cos{\\frac{n\\pi x}{L}}+b_{n}\\sin{\\frac{n\\pi x}{L}}\\right)$$</p>"
    </script>
<body>
```

Please note that users can also obtain the base64 encoded image of the equation from the original document by specifying `["equation"]`["equation"] in the `base64_encoding`base64_encoding field of the request body.

### Four-decimal format coordinates

Since [document-parse-240910](/docs/models#document-parse-240910)document-parse-240910, users can employ relative coordinates when drawing bounding boxes or cropping elements from input documents. The absolute position can be calculated by multiplying the `x`x and `y`y values in the `coordinates`coordinates field of each item by the width and height of the requested image.

```
"coordinates": [
    {
      "x": 0.0276,
      "y": 0.0178
    },
    {
      "x": 0.1755,
      "y": 0.0178
    },
    {
      "x": 0.1755,
      "y": 0.0641
    },
    {
      "x": 0.0276,
      "y": 0.0641
    }
]
```

## Tips and tricks

### Split a long PDF into shorter PDFs

Many PDF files are long, and sometimes goes beyond 100 pages which is the maximum page limit for the Document Parse API.
To process such long documents, or even to get faster responses for easier debugging, we can split our long PDF to shorter PDFs.
[Given a PDF file](https://arxiv.org/pdf/2312.15166.pdf)Given a PDF file `paper.pdf`paper.pdf,
run the code below to split a PDF into shorter PDFs and save them to separate files.
Note that we saved the example PDF file above and named it to `paper.pdf`paper.pdf.

```
"""
Requirements: `pip install pymupdf` to import fitz
"""
 
import os
import fitz
 
def split_pdf(input_file, batch_size):
    # Open input_pdf
    input_pdf = fitz.open(input_file)
    num_pages = len(input_pdf)
    print(f"Total number of pages: {num_pages}")
 
    # Split input_pdf
    for start_page in range(0, num_pages, batch_size):
        end_page = min(start_page + batch_size, num_pages) - 1
 
        # Write output_pdf to file
        input_file_basename = os.path.splitext(input_file)[0]
        output_file = f"{input_file_basename}_{start_page}_{end_page}.pdf"
        print(output_file)
        with fitz.open() as output_pdf:
            output_pdf.insert_pdf(input_pdf, from_page=start_page, to_page=end_page)
            output_pdf.save(output_file)
 
    # Close input_pdf
    input_pdf.close()
 
# Input arguments
input_file = "paper.pdf"  # Replace with a file of your own
batch_size = 10  # Maximum available value is 100
split_pdf(input_file, batch_size)
```

You can see resulting files in the terminal as follows.

```
$ ls paper*
paper.pdf        paper_0_9.pdf  paper_10_12.pdf
```

### Crop and save any element to separate image files

Document Parse offers base64 encoding for layout elements that users wish to extract as images. Let's attempt to extract all figures and save them as image files. In the code provided in Step 4 above, you can easily add `{'base64_encoding': '["figure"]'}`{'base64_encoding': '["figure"]'} to the request body, and the API will return a base64 encoded string for all figure elements. The following code then parses the response and saves the first figure to an image file.

```
"""
Requirements: `pip install requests`
"""
 
from glob import glob
import json
import os
import requests
 
API_KEY = "up_*************************K6ya"
 
def call_document_parse(input_file, output_file):
    # Send request
    response = requests.post(
        "https://api.upstage.ai/v1/document-digitization",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data={"base64_encoding": "['figure']", "model": "document-parse"}, # base64 encoding for cropped image of the figure category.
        files={"document": open(input_file, "rb")})
 
    # Save response
    if response.status_code == 200:
        with open(output_file, "w") as f:
            json.dump(response.json(), f, ensure_ascii=False)
    else:
        raise ValueError(f"Unexpected status code {response.status_code}.")
 
# Find all shorter PDFs related to input_file
input_file = "paper.pdf"
short_input_files = glob(os.path.splitext(input_file)[0] + "_*.pdf")
 
# Send request and save response for all shorter PDFs
for short_input_file in short_input_files:
    print(short_input_file)
    short_output_file = os.path.splitext(short_input_file)[0] + ".json"
    call_document_parse(short_input_file, short_output_file)
```

```
import json
import base64
 
# Input parameters
json_file = "paper_0_9.json"
output_file = "paper_cropped_figure.png"
 
# Load JSON file to get bounding box of the first figure
with open(json_file, "r") as f:
    data = json.load(f)
 
    # Get bounding box for the first figure and crop the image
    for element in data["elements"]:
        if element["category"] == "figure":
            with open (output_file, 'wb') as fh:
                fh.write(base64.decodebytes(str.encode(element["base64_encoding"])))
            break
```

The resulting figure can be seen as follows.

*Figure: The cropped figure*

### Chunk the output into segments

You can use each HTML tag as a chunk, but if you want to fully utilize a LLM's context length, you can use length-based chunking as follows.

```
def get_chunks(lines, max_context_length=4096):
    chunks = []
    current_chunk = []
 
    for line in lines:
        if len(" ".join(current_chunk + [line])) <= max_context_length:
            current_chunk.append(line)
        else:
            chunks.append(current_chunk)
            current_chunk = [line]
 
    if current_chunk:
        chunks.append(current_chunk)
    return chunks
 
with open("paper.html", "r") as f:
    lines = f.read().split("\n")
 
chunks = get_chunks(lines, max_context_length=1024)
print(chunks[0])
```

## Example

### Synchronous API

**Request**Request

*Figure: invoice.png*

```
# pip install -qU langchain-core langchain-upstage
 
import os
from langchain_upstage import UpstageDocumentParseLoader
 
os.environ["UPSTAGE_API_KEY"] = "up_*************************K6ya"
 
file_path = "YOUR_FILE_NAME"
loader = UpstageDocumentParseLoader(file_path, ocr="force")
 
pages = loader.load()  # or loader.lazy_load()
for page in pages:
    print(page)
```

**Response**Response

```
{
  "api": "2.0",
  "content": {
    "html": "<h1 id='0' style='font-size:22px'>INVOICE</h1>\n<h1 id='1' style='font-size:20px'>Company<br>Upstage</h1>\n<br><h1 id='2' style='font-size:18px'>Invoice ID</h1>\n<br><h1 id='3' style='font-size:14px'>휴 INV-AJ355548</h1>\n<h1 id='4' style='font-size:18px'>Invoice Date</h1>\n<br><h1 id='5' style='font-size:18px'>9/7/1992</h1>\n<h1 id='6' style='font-size:16px'>Mamo<br>Lucy Park</h1>\n<h1 id='7' style='font-size:18px'>Address</h1>\n<br><h1 id='8' style='font-size:16px'>7 Pepper Wood Street, 130 Stone Comer<br>Terrace<br>Wilkes Barre, Pennsylvania, 18768<br>United States</h1>\n<h1 id='9' style='font-size:16px'>Email</h1>\n<br><h1 id='10' style='font-size:16px'>Ikitchenman0@arizona.edu</h1>\n<br><h1 id='11' style='font-size:20px'>Service Details Form</h1>\n<h1 id='12' style='font-size:16px'>Name<br>Sung Kim</h1>\n<h1 id='13' style='font-size:16px'>260 'ess<br>Gwangovolungang:co 338, Gyeongg do.<br>Sanghyeon-dong, Sui-gu<br>Yongin-si, South Korea</h1>\n<h1 id='14' style='font-size:18px'>Additional Request</h1>\n<br><p id='15' data-category='paragraph' style='font-size:14px'>Vivamus vestibulum sagittis sapien. Cum sociis natoque<br>penatibus 항목 magnis dfs parturient montes, nascetur ridiculus<br>mus.</p>\n<h1 id='16' style='font-size:14px'>TERMS AND CONDITIONS</h1>\n<p id='17' data-category='list' style='font-size:14px'>L TM Seir that not be lable 1층 the Buyer drectly indirectly for any loun or damage sufflered by 전액 Buyer<br>2. The 별 www. the product for ore 과 관한 from the date 설 shipment.<br>3. Any ourchase order received by ~ sele - be interpreted 추가 accepting the offer Ma the 18% offer writing The buyer may<br>purchase 15 The offer My the Terms and Conditions the Seller included The offer</p>",
    "markdown": "",
    "text": ""
  },
  "elements": [
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='0' style='font-size:22px'>INVOICE</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0648,
          "y": 0.0517
        },
        {
          "x": 0.2405,
          "y": 0.0517
        },
        {
          "x": 0.2405,
          "y": 0.0953
        },
        {
          "x": 0.0648,
          "y": 0.0953
        }
      ],
      "id": 0,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='1' style='font-size:20px'>Company<br>Upstage</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0657,
          "y": 0.2651
        },
        {
          "x": 0.1606,
          "y": 0.2651
        },
        {
          "x": 0.1606,
          "y": 0.3168
        },
        {
          "x": 0.0657,
          "y": 0.3168
        }
      ],
      "id": 1,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<br><h1 id='2' style='font-size:18px'>Invoice ID</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.5712,
          "y": 0.0748
        },
        {
          "x": 0.671,
          "y": 0.0748
        },
        {
          "x": 0.671,
          "y": 0.101
        },
        {
          "x": 0.5712,
          "y": 0.101
        }
      ],
      "id": 2,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<br><h1 id='3' style='font-size:14px'>휴 INV-AJ355548</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.788,
          "y": 0.076
        },
        {
          "x": 0.9287,
          "y": 0.076
        },
        {
          "x": 0.9287,
          "y": 0.0972
        },
        {
          "x": 0.788,
          "y": 0.0972
        }
      ],
      "id": 3,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='4' style='font-size:18px'>Invoice Date</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.572,
          "y": 0.1232
        },
        {
          "x": 0.6941,
          "y": 0.1232
        },
        {
          "x": 0.6941,
          "y": 0.1484
        },
        {
          "x": 0.572,
          "y": 0.1484
        }
      ],
      "id": 4,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<br><h1 id='5' style='font-size:18px'>9/7/1992</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.8525,
          "y": 0.1224
        },
        {
          "x": 0.9293,
          "y": 0.1224
        },
        {
          "x": 0.9293,
          "y": 0.1468
        },
        {
          "x": 0.8525,
          "y": 0.1468
        }
      ],
      "id": 5,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='6' style='font-size:16px'>Mamo<br>Lucy Park</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0658,
          "y": 0.3331
        },
        {
          "x": 0.15,
          "y": 0.3331
        },
        {
          "x": 0.15,
          "y": 0.3846
        },
        {
          "x": 0.0658,
          "y": 0.3846
        }
      ],
      "id": 6,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='7' style='font-size:18px'>Address</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0662,
          "y": 0.4061
        },
        {
          "x": 0.1482,
          "y": 0.4061
        },
        {
          "x": 0.1482,
          "y": 0.4286
        },
        {
          "x": 0.0662,
          "y": 0.4286
        }
      ],
      "id": 7,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<br><h1 id='8' style='font-size:16px'>7 Pepper Wood Street, 130 Stone Comer<br>Terrace<br>Wilkes Barre, Pennsylvania, 18768<br>United States</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.067,
          "y": 0.4332
        },
        {
          "x": 0.3962,
          "y": 0.4332
        },
        {
          "x": 0.3962,
          "y": 0.5173
        },
        {
          "x": 0.067,
          "y": 0.5173
        }
      ],
      "id": 8,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='9' style='font-size:16px'>Email</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0656,
          "y": 0.5326
        },
        {
          "x": 0.1235,
          "y": 0.5326
        },
        {
          "x": 0.1235,
          "y": 0.5579
        },
        {
          "x": 0.0656,
          "y": 0.5579
        }
      ],
      "id": 9,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<br><h1 id='10' style='font-size:16px'>Ikitchenman0@arizona.edu</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0654,
          "y": 0.5614
        },
        {
          "x": 0.2874,
          "y": 0.5614
        },
        {
          "x": 0.2874,
          "y": 0.5834
        },
        {
          "x": 0.0654,
          "y": 0.5834
        }
      ],
      "id": 10,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<br><h1 id='11' style='font-size:20px'>Service Details Form</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.5727,
          "y": 0.2112
        },
        {
          "x": 0.8149,
          "y": 0.2112
        },
        {
          "x": 0.8149,
          "y": 0.2417
        },
        {
          "x": 0.5727,
          "y": 0.2417
        }
      ],
      "id": 11,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='12' style='font-size:16px'>Name<br>Sung Kim</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.573,
          "y": 0.2657
        },
        {
          "x": 0.6563,
          "y": 0.2657
        },
        {
          "x": 0.6563,
          "y": 0.3177
        },
        {
          "x": 0.573,
          "y": 0.3177
        }
      ],
      "id": 12,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='13' style='font-size:16px'>260 'ess<br>Gwangovolungang:co 338, Gyeongg do.<br>Sanghyeon-dong, Sui-gu<br>Yongin-si, South Korea</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.5724,
          "y": 0.3401
        },
        {
          "x": 0.891,
          "y": 0.3401
        },
        {
          "x": 0.891,
          "y": 0.4232
        },
        {
          "x": 0.5724,
          "y": 0.4232
        }
      ],
      "id": 13,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='14' style='font-size:18px'>Additional Request</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0648,
          "y": 0.6681
        },
        {
          "x": 0.2482,
          "y": 0.6681
        },
        {
          "x": 0.2482,
          "y": 0.6962
        },
        {
          "x": 0.0648,
          "y": 0.6962
        }
      ],
      "id": 14,
      "page": 1
    },
    {
      "category": "paragraph",
      "content": {
        "html": "<br><p id='15' data-category='paragraph' style='font-size:14px'>Vivamus vestibulum sagittis sapien. Cum sociis natoque<br>penatibus 항목 magnis dfs parturient montes, nascetur ridiculus<br>mus.</p>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.4191,
          "y": 0.6684
        },
        {
          "x": 0.9132,
          "y": 0.6684
        },
        {
          "x": 0.9132,
          "y": 0.7332
        },
        {
          "x": 0.4191,
          "y": 0.7332
        }
      ],
      "id": 15,
      "page": 1
    },
    {
      "category": "heading1",
      "content": {
        "html": "<h1 id='16' style='font-size:14px'>TERMS AND CONDITIONS</h1>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0649,
          "y": 0.8303
        },
        {
          "x": 0.2506,
          "y": 0.8303
        },
        {
          "x": 0.2506,
          "y": 0.8523
        },
        {
          "x": 0.0649,
          "y": 0.8523
        }
      ],
      "id": 16,
      "page": 1
    },
    {
      "category": "list",
      "content": {
        "html": "<p id='17' data-category='list' style='font-size:14px'>L TM Seir that not be lable 1층 the Buyer drectly indirectly for any loun or damage sufflered by 전액 Buyer<br>2. The 별 www. the product for ore 과 관한 from the date 설 shipment.<br>3. Any ourchase order received by ~ sele - be interpreted 추가 accepting the offer Ma the 18% offer writing The buyer may<br>purchase 15 The offer My the Terms and Conditions the Seller included The offer</p>",
        "markdown": "",
        "text": ""
      },
      "coordinates": [
        {
          "x": 0.0679,
          "y": 0.8717
        },
        {
          "x": 0.9261,
          "y": 0.8717
        },
        {
          "x": 0.9261,
          "y": 0.9558
        },
        {
          "x": 0.0679,
          "y": 0.9558
        }
      ],
      "id": 17,
      "page": 1
    }
  ],
  "model": "document-parse-250404",
  "usage": {
    "pages": 1
  }
}
```

### Asynchronous API

#### How it works

Users can submit an inference request for an image or a PDF document with up to 1000 pages using the [asynchronous inference request API](#inference-request)asynchronous inference request API in Document Parse. Upon receiving the request, the API immediately returns a Request ID. After the input file is transferred and validated, it is divided into batches of 10 pages each, and inference is performed on each batch. Users can check the status of each batch in real-time using the response from the [asynchronous inference request
API](#inference-request)asynchronous inference request
API. The inference results of each batch can be downloaded using the provided `download_url`download_url in the response. The results will be available for downloading for 30 days from the time of the request.

#### Inference request

**Request**Request

```
import requests
 
api_key = "up_*************************K6ya"
filename = "invoice.png"
 
url = "https://api.upstage.ai/v1/document-digitization/async"
headers = {"Authorization": f"Bearer {api_key}"}
files = {"document": open(filename, "rb")}
data = {"model": "document-parse"}
response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

**Response**Response

```
{
    "request_id": "e7b1b3b0-1b3b-4b3b-8b3b-1b3b3b3b3b3b"
}
```

#### Retrieve inference results

Retrieve inference results by calling this API.

**Request**Request

```
import requests
 
api_key = "up_*************************K6ya"
 
url = "https://api.upstage.ai/v1/document-digitization/requests/REQUEST_ID"
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(url, headers=headers)
print(response.json())
```

**Response**Response

```
 
{
    "id": "e7b1b3b0-1b3b-4b3b-8b3b-1b3b3b3b3b3b",
    "status": "completed",
    "model": "document-parse",
    "failure_message": "",
    "total_pages": 28,
    "completed_pages": 28,
    "batches": [
        {
            "id": 0,
            "model": "document-parse-250404",
            "status": "completed",
            "failure_message": "",
            "download_url": "https://download-url",
            "start_page": 1,
            "end_page": 10,
            "requested_at": "2024-07-01T14:47:01.863880448Z",
            "updated_at": "2024-07-01T14:47:15.901662097Z"
        },
        {
            "id": 1,
            "model": "document-parse-250404",
            "status": "completed",
            "failure_message": "",
            "download_url": "https://download-url",
            "start_page": 11,
            "end_page": 20,
            "requested_at": "2024-07-01T14:47:01.863880448Z",
            "updated_at": "2024-07-01T14:47:13.59782266Z"
        },
        {
            "id": 2,
            "model": "document-parse-250404",
            "status": "completed",
            "failure_message": "",
            "download_url": "https://download-url",
            "start_page": 21,
            "end_page": 28,
            "requested_at": "2024-07-01T14:47:01.863880448Z",
            "updated_at": "2024-07-01T14:47:37.061016766Z"
        }
    ],
    "requested_at": "2024-07-01T14:47:01.863880448Z",
    "completed_at": "2024-07-01T14:47:43.023542045Z"
}
```

#### Retrieve inference history

**Request**Request

```
import requests
 
api_key = "up_*************************K6ya"
 
url = "https://api.upstage.ai/v1/document-digitization/requests"
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(url, headers=headers)
print(response.json())
```

**Response**Response

```
{
    "requests": [
        {
            "id": "e7b1b3b0-1b3b-4b3b-8b3b-1b3b3b3b3b3b",
            "status": "completed",
            "model": "document-parse",
            "requested_at": "2024-07-01T14:47:01.863880448Z",
            "completed_at": "2024-07-01T14:47:43.023542045Z"
        }
    ]
}
```

#### Handling errors

In Document Parse Async APIs, errors can occur in three different scenarios: request errors, batch-inference errors, or failures to retrieve the request result.

1. **Request errors**Request errors: This error occurs when the input document cannot be handled by the API or if there's an error during processing, such as image conversion or page split. In case of a request failure, instead of returning a request ID, the API returns an object with error code and message. ``` {
    code: xxx, # http status code
    message: "", # detail error message
  } ``` The table below shows the error message and code for typical error cases. | error message | http status code | | --- | --- | | invalid model name | 400 | | no document in the request | 400 | | uploaded document is too large. max allowed size is 50MB | 413 | | unsupported document format | 415 |

2. **Batch inference error**Batch inference error: Due to the engine dividing the input document into batches of 10 pages each, each batch may have a different status for model inference. As the input file has already been validated before inference, batch inference errors are most likely caused by internal server errors. When this occurs, the API response for retrieving the result will show a `failed`failed status in the `batches`batches field with a `failure_message`failure_message. The below code block shows the schema of batches field in the API response for inference result. ``` "batches": {
    "id": number;
    "model": string;
    "status": scheduled | started | completed | failed | retrying;
    "failure_message": string;
    "download_url": string;
    "start_page": number;
    "end_page": number;
    "requested_at": date;
    "updated_at": date;
  }[] ```

3. **Failures to retrieve the request result**Failures to retrieve the request result: Normally, this error can occur when the `download_url`download_url for each batch fails to generate. Due to security reasons, the download URL is only valid for 15 minutes and a new one is generated every time the user retrieves the inference result. When a user submits a long document, the server needs to create a download URL for each batch, and sometimes the server may struggle to create a high number of pre-signed URLs.
