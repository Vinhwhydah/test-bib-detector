pipeline {
  environment {
    REPOPRODUCTION = 'asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend'
    REPODEV = 'asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend'
    REPOSTAGING = 'asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend'
  }
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    some-label: dind-agent
spec:
  serviceAccountName: jenkins-admin
  dnsConfig:
    namesevers:
      - 8.8.8.8
  containers:
  - name: dind
    image: docker:latest
    imagePullPolicy: Always
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
      - name: docker-graph-storage
        mountPath: /var/lib/docker
  - name: trivy
    image: bitnami/trivy
    command: ["sleep"]
    args: ["99999d"]
    tty: true
    securityContext:
      runAsUser: 0  
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  - name: helm
    image: alpine/helm
    imagePullPolicy: Always
    tty: true
    command: ["cat"]
    securityContext:
      runAsUser: 0
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
    securityContext:
      runAsUser: 0
    volumes:
    - name: docker-sock
      hostPath:
        path: /var/run/docker.sock
  volumes:
    - name: docker-graph-storage
      emptyDir: {}
    - name: docker-sock
      hostPath:
        path: /var/run/docker.sock
"""
    }
  }
  stages {
    stage('Prepare') {
      steps {
        script {
          if (env.BRANCH_NAME == 'main') {
            configFileProvider([configFile(fileId: 'file-env', variable: 'env')]) {
              sh 'pwd'
              sh 'ls'
              sh "scp ${env.env} .env"
            }
            configFileProvider([configFile(fileId: 'e813b8ad-87aa-405d-8eee-4b7817075c80', variable: 'json')]) {
              sh "scp ${env.json} bib_detector_credential.json"
            }
            sh 'ls -a'
            sh 'cat .env'
            sh 'cat bib_detector_credential.json'
          } else if (env.BRANCH_NAME =="dev"){
            configFileProvider([configFile(fileId: 'file-env', variable: 'env')]) {
              sh "scp ${env.env} .env"
            }
            configFileProvider([configFile(fileId: 'e813b8ad-87aa-405d-8eee-4b7817075c80', variable: 'json')]) {
              sh "scp ${env.json} bib_detector_credential.json"
            }
          } else if (env.BRANCH_NAME =="staging"){
            configFileProvider([configFile(fileId: 'file-env', variable: 'env')]) {
              sh "scp ${env.env} .env"
            }
            configFileProvider([configFile(fileId: 'e813b8ad-87aa-405d-8eee-4b7817075c80', variable: 'json')]) {
              sh "scp ${env.json} bib_detector_credential.json"
            }
          }  
        } 
      }
    }
    stage('Build My Docker Image') {
      steps {
        container('dind') {
          script {
            if (env.BRANCH_NAME == 'main') {
              sh 'docker info'
              sh 'docker build --network=host -t $REPOPRODUCTION:$GIT_COMMIT-$BUILD_NUMBER .'
              sh 'docker images'
            } else if (env.BRANCH_NAME =="dev"){
              sh 'docker info'
              sh 'docker build --network=host -t asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER .'
              sh 'docker images'
            } else if (env.BRANCH_NAME =="dev"){
              sh 'docker info'
              sh 'docker build --network=host -t asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER .'
              sh 'docker images'
            }
          }
        }
      }
    }
    stage('Login ArtifactRegistry') {
      steps {
        container('dind') {
          script {
            if (env.BRANCH_NAME == 'main') {
              configFileProvider([configFile(fileId: 'e105c6a4-032a-4295-94dc-8e4ea4210e89', variable: 'login')]) {
                sh "cat ${env.login} | docker login -u _json_key --password-stdin https://asia-southeast1-docker.pkg.dev"
              }
            } else if (env.BRANCH_NAME =="dev"){
              configFileProvider([configFile(fileId: 'e105c6a4-032a-4295-94dc-8e4ea4210e89', variable: 'login')]) {
                sh "cat ${env.login} | docker login -u _json_key --password-stdin https://asia-southeast1-docker.pkg.dev"
              }
            } else if (env.BRANCH_NAME =="staging"){
              configFileProvider([configFile(fileId: 'e105c6a4-032a-4295-94dc-8e4ea4210e89', variable: 'login')]) {
                sh "cat ${env.login} | docker login -u _json_key --password-stdin https://asia-southeast1-docker.pkg.dev"
              }
            }
          }  
        }
      }
    }
    stage('Docker Push') {
      steps {
        container('dind') {
          script {
            if (env.BRANCH_NAME == 'main') {
              sh "docker push asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
            } else if (env.BRANCH_NAME =="dev"){
              sh "docker push asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
            } else if (env.BRANCH_NAME =="staging"){
              sh "docker push asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
            }
          }
        } 
      }
    }
    stage('Connect Cluster And Deploy ^^'){
      steps {
        container('kubectl'){
          script {
            if (env.BRANCH_NAME == 'main'){
              withCredentials([file(credentialsId: 'testdeploy', variable: 'TMPKUBECONFIG')]) {
                sh "cat \$TMPKUBECONFIG"
                sh "cp \$TMPKUBECONFIG /.kube/config"
                sh "kubectl config set-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins --user=jenkins --cluster=gke_system-dev-3749090_asia-southeast1_test-cicd --namespace=staging"
                sh "kubectl config use-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins"
                sh "kubectl get pods"
                sh "kubectl set image deployment --namespace=staging backend backend=asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
              }
            } else if (env.BRANCH_NAME =="dev"){
              withCredentials([file(credentialsId: 'testdeploy', variable: 'TMPKUBECONFIG')]) {
                sh "cat \$TMPKUBECONFIG"
                sh "cp \$TMPKUBECONFIG /.kube/config"
                sh "kubectl config set-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins --user=jenkins --cluster=gke_system-dev-3749090_asia-southeast1_test-cicd --namespace=staging"
                sh "kubectl config use-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins"
                sh "kubectl get pods"
              }
            } else if (env.BRANCH_NAME =="staging"){
              withCredentials([file(credentialsId: 'testdeploy', variable: 'TMPKUBECONFIG')]) {
                sh "cat \$TMPKUBECONFIG"
                sh "cp \$TMPKUBECONFIG /.kube/config"
                sh "kubectl config set-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins --user=jenkins --cluster=gke_system-dev-3749090_asia-southeast1_test-cicd --namespace=staging"
                sh "kubectl config use-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins"
                sh "kubectl get pods"
                sh "kubectl set image deployment --namespace=staging backend backend=asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
              }
            }  
          }
        }
      }
    }
    stage('testhelm') {
      steps {
        container('helm'){
          script {
            if (env.BRANCH_NAME == "main") {
              withCredentials([file(credentialsId: 'testdeploy', variable: 'TMPKUBECONFIG')]) {
                sh """
                export KUBECONFIG=\${TMPKUBECONFIG}
                helm upgrade --install -f values.dev.yaml --namespace staging
                helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
                helm install my-nginx ingress-nginx/ingress-nginx
                """
              }
            } else if (env.BRANCH_NAME =="dev"){
              def namepsace="stage"
              withCredentials([file(credentialsId: 'kubeconfig-stage', variable: 'config')]) {
                sh """
                export KUBECONFIG=\${config}
                helm upgrade --install -f values.dev.yaml --namespace ${namespace}"
                """
              }
            } else if (env.BRANCH_NAME =="staging"){
              def namepsace="prod"
              withCredentials([file(credentialsId: 'kubeconfig-prod', variable: 'config')]) {
                sh """
                export KUBECONFIG=\${config}
                helm upgrade --install -f values.dev.yaml --namespace ${namespace}"
                """
              }
            }
          }
        }
      }
    } 
  }
}
    // stage('Docker Push') {
    //   when {
    //     expression { env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'test' }
    //   }
    //   steps {
    //     container('dind') {
    //       sh "docker push asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
    //     }
    //   }
    // }
//     stage('Connect Cluster And Deploy ^^'){
//       when {
//         expression { env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'test' }
//       }
//       steps {
//         container('kubectl'){
//           withCredentials([file(credentialsId: 'testdeploy', variable: 'TMPKUBECONFIG')]) {
//             sh "cat \$TMPKUBECONFIG" 
//             sh "cp \$TMPKUBECONFIG /.kube/config"
//             sh "ls"
//             sh "kubectl config set-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins --user=jenkins --cluster=gke_system-dev-3749090_asia-southeast1_test-cicd --namespace=staging"
//             sh "kubectl config use-context gke_system-dev-3749090_asia-southeast1_test-cicd-jenkins"
//             sh "kubectl get pods"
//             sh "kubectl apply -f DeloymentBackend_Bizz.yaml"
//             sh "kubectl apply -f DeloymentDetect_Bizz.yaml"
//             sh "kubectl apply -f DeloymentFrontend_Bizz.yaml"
//             sh "kubectl set image deployment --namespace=staging backend backend=asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
//           }
//         }
//       }
//     }
//     stage('Test Helm') {
//       when {
//         expression { env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'production' }
//       }
//       steps {
//         container('helm') {
//           script {
//             if (env.BRANCH_NAME == "main") {
//               def namepsace="staging"
//               withCredentials([file(credentialsId: 'testdeploy', variable: 'TMPKUBECONFIG')]) {
//                 sh "export KUBECONFIG=\${TMPKUBECONFIG}"
//                 sh "helm version"
//                 sh "helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx"
//                 sh "helm install my-nginx ingress-nginx/ingress-nginx"
//               }
//             }
//           }
//         }
//       }
//     }
//   }
// }


    // stage('Scan Docker Image') {
    //   when {
    //     expression { env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'production' }
    //   }
    //   steps {
    //     container('trivy') {
    //       sh "trivy image asia-southeast1-docker.pkg.dev/system-dev-3749090/repotest/core-backend:$GIT_COMMIT-$BUILD_NUMBER"
    //     }
    //   }
    // }
