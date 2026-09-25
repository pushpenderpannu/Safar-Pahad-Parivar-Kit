@echo off
cd /d "F:\Video Editing\_Safar Pahad Parivar Kit\Tools"
set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
(
.venv\Scripts\python.exe spp_word_timing.py _work\job_cues.json _work\out_cues.json
echo RUN_DONE %TIME%
) > _work\run_cues_log.txt 2>&1
