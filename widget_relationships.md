graph TD
    subgraph "答案 (Answer)"
        AnswerSheet -- "contains" --> AnswerSearchBar
        AnswerSheet -- "contains 8x" --> AnswerSheetPageWidget
        AnswerSheetPageWidget -- "contains" --> ScrollableAnswerEditor
        ScrollableAnswerEditor -- "contains" --> LineNumberWidget
    end

    subgraph "PDF注釈 (Annotation)"
        PDFDisplayLabel -- "creates" --> TextAnnotationWidget
        PDFDisplayLabel -- "creates" --> ShapeAnnotationWidget
    end

    subgraph "その他 (Misc)"
        MemoWindow
    end

    subgraph "設定 (Config)"
        TextEditorConfig
    end

    %% パラメータの流れ
    TextEditorConfig -- "config" --> AnswerSheetPageWidget
    AnswerSheetPageWidget -- "config" --> ScrollableAnswerEditor