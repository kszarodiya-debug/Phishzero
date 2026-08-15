# Email text model

This component classifies email text using the explicit `subject + body` input, a TF-IDF vectorizer, and Logistic Regression. It produces a predicted class, the probability of that predicted class, confidence (currently the same class probability), and a model version.

## Dataset policy

Training never downloads a dataset automatically. Provide a documented local copy of a legitimate public or authorized dataset. A suitable public source is the SpamAssassin Public Corpus; it must be downloaded and converted manually by the operator. The repository does not include that corpus and does not claim production accuracy from the test fixture.

The expected UTF-8 CSV format is:

```csv
subject,body,label
"Meeting reminder","The meeting starts at 10:00.",ham
"Claim your prize","You have won a prize.",spam
```

Required columns:

- `subject` — email subject; empty values are allowed when `body` is present.
- `body` — plain-text email body; empty values are allowed when `subject` is present.
- `label` — non-empty class label such as `ham` or `spam`; at least two classes are required.

Train from the backend directory with an explicit local path:

```powershell
.\.venv\Scripts\python.exe -m app.ml.train_text_model --csv C:\path\to\email_dataset.csv
```

Artifacts are written to `backend/app/ml/artifacts/` by default:

- `email_text_model.joblib` — trained pipeline and metadata
- `email_text_metrics.json` — accuracy, precision, recall, F1, and confusion matrix
- `email_text_confusion_matrix.csv` — labeled confusion matrix

The small CSV under `backend/tests/fixtures/` is only an automated-test fixture. It is not a production training dataset and no production artifact is generated from it.

## Static URL model

The URL model uses a Random Forest over static features derived only from the URL string. It never resolves or visits URLs. The expected UTF-8 CSV format is:

```csv
url,label
https://www.example.com/account,benign
http://bit.ly/verify-now,phishing
```

Required columns:

- `url` — an absolute `http` or `https` URL.
- `label` — a non-empty class label such as `benign` or `phishing`; at least two classes are required.

The analyzer produces these integer features: URL length, hostname length, path length, subdomain count, IP-address presence, `@` presence, hyphen count, digit count, special-character count, HTTPS presence, and a known-shortener pattern flag. Subdomains are counted as hostname labels excluding the final two labels. Special characters are all non-alphanumeric characters. Shortener detection uses a static known-hostname list and performs no DNS or network lookup.

Train from a manually prepared local CSV; no dataset is downloaded automatically:

```powershell
.\.venv\Scripts\python.exe -m app.ml.train_url_model --csv C:\path\to\url_dataset.csv
```

An authorized or public URL dataset such as a manually prepared local export from PhishTank or URLhaus may be used, subject to its terms and labeling quality. The repository does not include such a dataset and does not claim production accuracy from the test fixture.

URL artifacts are written to `backend/app/ml/artifacts/` by default as `url_model.joblib`, `url_model_metrics.json`, and `url_model_confusion_matrix.csv`.
