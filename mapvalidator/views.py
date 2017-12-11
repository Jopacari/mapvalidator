from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import validators
import re
import datetime
import logging


def home(request):
    # Get an instance of a logger
    logger = logging.getLogger(__name__)
    if request.method == 'POST' and request.FILES and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        logger.info ("Received file: " + myfile.name)
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        line_number = 0
        errors = 0
        max_errors = 100
        result_output = []
        line_format = re.compile("(http://(?:[\w\-_]+\.)*([\w\-_]+\.[\w\-_]+)(?:/.*|\?.*|))\ (https://www.farfetch.com.*);")
        base_domain_format = re.compile("http://(?:[\w\-_]+\.)*([\w\-_]+\.[\w\-_]+)(?:/|\?|\ )")
        base_origin_domain = 'not_detected_yet'
        result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - Started processing file.")
        lines = set()
        try:
            with open(fs.path(filename),'rt', errors="surrogateescape") as f:
                for line in f:
                    line = line.replace("\r", "").replace("\n", "")
                    if errors >= max_errors:
                        log_line = "At least " + str(max_errors) + " errors found. Processing was interrupted."
                        result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                        logger.critical(log_line)
                        break;
                    line_number += 1
                    urls = line_format.search(line)
                    if line_number == 1:
                        #first line let's try to detect the base of the origin domain to catch more errors :-)
                        bases = base_domain_format.search(line)
                        if bases:
                            # we found a valid base
                            base_origin_domain = bases.group(1)
                            log_line = "Origin base domain detected: " + base_origin_domain
                            result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                            logger.info(log_line)
                    if urls:
                        #next we test the urls
                        if not validators.url(urls.group(1)):
                            log_line = "Line " + str(line_number) + ": Url " + urls.group(1).encode('utf8','replace').decode('utf-8') + " is invalid."
                            result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                            logger.error(log_line)
                            errors += 1
                        else:
                            #let's validate the origin base domain
                            if base_origin_domain != urls.group(2):
                                log_line = "Line " + str(line_number) + ": Url " + urls.group(1).encode('utf8','replace').decode('utf-8') + " is not from base domain " + base_origin_domain + "."
                                result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                                logger.error(log_line)
                                errors += 1
                            else:
                                if not urls.group(1) in lines:
                                    lines.add(urls.group(1))
                                else:
                                    # we found a duplicate
                                    log_line = "Line " + str(line_number) + ": Origin url is duplicated. " + urls.group(1).encode('utf8','replace').decode('utf-8')
                                    result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                                    logger.error(log_line)
                                    errors += 1
                        if not validators.url(urls.group(3)):
                            log_line = "Line " + str(line_number) + ": Url " + urls.group(3).encode('utf8','replace').decode('utf-8') + " is invalid."
                            result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                            logger.error(log_line)
                            errors += 1
                    
                    else:
                        log_line = "Line " + str(line_number) + ": Bad line line_format or invalid character. " + line.encode('utf8','replace').decode('utf-8')
                        result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                        logger.error(log_line)
                        errors += 1
                    
                log_line = "Finished processing file. Found " + str(errors) + " error(s)."
                result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line )
                logger.info(log_line)
        except Exception as e:
            log_line = " - File has invalid characters at line "+ str(line_number) + ". Parsing can't proceed. Process interrupted. "
            result_output.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - " +  log_line  + str(e))
            logger.critical(log_line,e)
        fs.delete(filename)
        return render(request, 'home.html', {'uploaded_file': myfile.name,'result_output':result_output, 'errors':errors})
        #return render(request, 'home.html', {'uploaded_file_url': uploaded_file_url, 'errors':len(result_output)})
    return render(request, 'home.html')
    
