DATASET = [
      "ant",
      "maven",
     "rhino",
      "closure",
      "chocopy",
      "gson",
      "jackson",
]
ALGORITHM = [
    "zest",
    "ei",
    "blind",
    "mix",
    "zeugma-linked",
    "zeugma-none",
    "bedivfuzz-structure",
    "bedivfuzz-simple",
]

GENERATOR = [
    'testWithGenerator',
]

TEST_CLASS_PREFIX = "edu.berkeley.cs.jqf.examples."
DATASET_TEST_CLASS_MAPPING = {
    "ant": TEST_CLASS_PREFIX + "ant.ProjectBuilderTest",
    "maven": TEST_CLASS_PREFIX + "maven.ModelReaderTest",
    "bcel": TEST_CLASS_PREFIX + "bcel.ParserTest",
    "closure": TEST_CLASS_PREFIX + "closure.CompilerTest",
    "rhino": TEST_CLASS_PREFIX + "rhino.CompilerTest",
    "chocopy": TEST_CLASS_PREFIX + "chocopy.SemanticAnalysisTest",
    "gson": TEST_CLASS_PREFIX + "gson.JsonTest",
    "jackson": TEST_CLASS_PREFIX + "jackson.JsonTest",
    "jython": TEST_CLASS_PREFIX + "jython.JythonInterpreterTest",
}
