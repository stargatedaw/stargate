
/*
void write_log(char * a_string)
{
    assert(a_string);
    char buff[LMS_LARGE_STRING];
    time_t now = time (0);
    strftime (buff, 100, "%Y-%m-%d %H:%M:%S.000", localtime (&now));

    strcat(buff, " - ");
    strcat(buff, a_string);

    FILE* pFile = fopen("sg-engine.log", "a");
    fprintf(pFile, "%s\n",buff);
    fclose(pFile);
}
*/
