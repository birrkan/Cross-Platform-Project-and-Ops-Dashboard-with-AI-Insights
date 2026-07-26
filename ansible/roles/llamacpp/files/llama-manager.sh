#!/bin/bash

# UI -------------
ACCENT="#D3A187f"
PRIMARY="#186560"

gum style \
  --foreground="$ACCENT" \
  --border=double \
  --border-foreground="$PRIMARY" \
  --align=center \
  --width=60 \
  --margin "1 2" \
"
░█░░░█░░░█▀█░█▄█░█▀█░░░█▀▀░█▀█░█▀█░█▀▀░█▀█░█░░░█▀▀
░█░░░█░░░█▀█░█░█░█▀█░░░█░░░█░█░█░█░▀▀█░█░█░█░░░█▀▀
░▀▀▀░▀▀▀░▀░▀░▀░▀░▀░▀░░░▀▀▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀▀░▀▀▀

@birrkan
"

# variables ---------------
gguf_model_directory="/opt/llama/models"

# main --------------------

while true; do
    mode=$(gum choose \
      --cursor.foreground="$ACCENT" \
      --selected.foreground="$PRIMARY" \
      --header "What do you want to do?" \
      "Run Server" \
      "Run CLI" \
      "Download New Model" \
      "Exit"
    )

    [ -z "$mode" ] && break
    [[ "$mode" == "Exit" ]] && break

    if [[ "$mode" == "Download New Model" ]]; then
        model=$(gum input \
          --placeholder "Enter HuggingFace model (e.g. author/model:quant)"
        )
        [ -z "$model" ] && continue
        llama download -hf "$model"
        continue
    fi

    mapfile -t gguf_list < <(find ${gguf_model_directory} -name "*.gguf")

    if [[ ${#gguf_list[@]} -eq 0 ]]; then
        gum style --foreground="#FF0000" "No .gguf files found in ${gguf_model_directory}"
        continue
    fi

    display_names=("← Back")
    for f in "${gguf_list[@]}"; do
        display_names+=("$(basename "$f")")
    done

    selected=$(gum choose \
      --cursor.foreground="$ACCENT" \
      --selected.foreground="$PRIMARY" \
      --header "Select a GGUF model" \
      "${display_names[@]}"
    )

    [ -z "$selected" ] && continue
    [[ "$selected" == "← Back" ]] && continue

    for f in "${gguf_list[@]}"; do
        if [[ "$(basename "$f")" == "$selected" ]]; then
            gguf_path="$f"
            break
        fi
    done

    if [[ "$mode" == "Run Server" ]]; then
        llama serve -m "$gguf_path" --host 0.0.0.0 -c 16384 --port 3535
    elif [[ "$mode" == "Run CLI" ]]; then
        llama run -m "$gguf_path" -c 16384
    fi
done

# -------- DONE --------

gum style \
    --foreground="$PRIMARY" \
    --border=rounded \
    --border-foreground="$ACCENT" \
    --align=center \
    --width=50 \
"✔"
