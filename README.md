# Diavgeia Open Data

This repository hosts a complete, reproducible collection of decisions published on the Greek **Diavgeia (Διαύγεια)** transparency portal.
It is part of an ongoing open-government and transparency research initiative focused on large-scale document extraction, structuring, and analysis.

## Repository Structure

The dataset is organized into three top-level folders:

### 1. `pdfs/`

Raw PDF files exactly as downloaded from Diavgeia.
These are unprocessed source documents and may contain scanned pages, mixed OCR quality, or embedded text.

### 2. `structured/`

Structured JSON files containing parsed metadata and normalized fields extracted from each Diavgeia decision.
Typical fields include:

* `ada` (ΑΔΑ – unique posting ID)
* `protocolNumber`
* `issueDate`
* `subject`
* `organizationId`, `unitIds`
* signatories
* decision type
* financial amounts (when applicable)
* classification tags
* links to raw/extracted text

This folder represents the *machine-readable* layer of the dataset.

### 3. `extracted/`

Plain-text files containing OCR or PDF-extracted text for each decision.
Content here is produced by a standardized extraction pipeline (PDF → text), used for downstream NLP, RAG systems, auditing tools, and research experiments.

## Purpose

This repository aims to enable:

* Large-scale analysis of public administration actions
* Transparency research and auditing
* Reproducible experiments in NLP, RAG, and document understanding

## Data Source

All documents are sourced from the official **Diavgeia** portal ([https://diavgeia.gov.gr/](https://diavgeia.gov.gr/)), which publishes public-sector decisions under Greek law.
The dataset here republishes and organizes this content for research and open-government purposes.

## Pipeline (High-Level)

1. Fetch metadata and documents from Diavgeia APIs
2. Download and store PDFs
3. Apply OCR/text extraction
4. Parse metadata and structure it into normalized JSON
5. Publish the dataset in reproducible form

A full pipeline description will be added soon.

## License / Legal Notice

Documents originate from the Greek public sector and fall under the legal provisions for open access under the Diavgeia framework.
This repository republishes them solely for research, transparency, and educational purposes.
Users should verify compliance with local regulations before redistribution.

## Contact

For questions, improvements, or collaboration proposals, please open an issue or contact us.
