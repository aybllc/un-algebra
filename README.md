# U/N Algebra: Uncertainty/Nominal Algebra Framework

[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

**U/N Algebra** is the complementary dual to N/U Algebra, representing quantities as **(u, n)** where uncertainty takes priority.

## Quick Start

### Python
\`\`\`python
from un_algebra.core import create_UN, hubble_UN_merge

early = create_UN(n_a=67.4, u_t=0.3, n_m=67.4, u_m=0.5)
late = create_UN(n_a=73.0, u_t=0.4, n_m=73.0, u_m=1.0)
result = hubble_UN_merge(early, late, tensor_distance=1.3)
\`\`\`

See [docs/](docs/) for full documentation.
