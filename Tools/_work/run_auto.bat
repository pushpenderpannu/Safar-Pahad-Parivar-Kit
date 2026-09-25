@echo off
cd /d "F:\Video Editing\_Safar Pahad Parivar Kit\Tools"
set PYTHONIOENCODING=utf-8
(
echo START %TIME%
.venv\Scripts\python.exe spp_word_timing.py _work\job_auto.json _work\out_auto.json
echo RUN_DONE %TIME%
) > _work\run_auto_log.txt 2>&1
